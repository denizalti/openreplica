'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Master class for all nodes
@copyright: See LICENSE
'''
import copy
import os, sys
import random, struct
import cPickle as pickle
import time, socket, select
from Queue import Queue
from optparse import OptionParser
from threading import Thread, RLock, Lock, Condition, Timer, Semaphore
from concoord.enums import *
from concoord.utils import *
from concoord.message import *
from concoord.pack import *
from concoord.pvalue import PValueSet
from concoord.connection import ConnectionPool,Connection

try:
    import dns.resolver, dns.exception
except:
    print("Install dnspython: http://www.dnspython.org/")

parser = OptionParser()
parser.add_option("-a", "--addr", action="store", dest="addr", help="addr for the node")
parser.add_option("-p", "--port", action="store", dest="port", type="int", help="port for the node")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port:type triple for the bootstrap peer")
parser.add_option("-f", "--objectfilename", action="store", dest="objectfilename", default='', help="client object file name")
parser.add_option("-c", "--objectname", action="store", dest="objectname", help="object name")
parser.add_option("-l", "--logger", action="store", dest="logger", default='', help="logger address")
parser.add_option("-o", "--configpath", action="store", dest="configpath", default='', help="config file path")
parser.add_option("-n", "--name", action="store", dest="domain", default='', help="domainname that the nameserver will accept queries for")
parser.add_option("-t", "--type", action="store", dest="type", default='', help="1: Master Nameserver 2: Slave Nameserver (requires a Master) 3:Route53 (requires a Route53 zone)")
parser.add_option("-m", "--master", action="store", dest="master", default='', help="ipaddr:port for the master nameserver")
parser.add_option("-d", "--debug", action="store_true", dest="debug", default=False, help="debug on/off")
(options, args) = parser.parse_args()

class Node():
    """Node encloses the basic Node behaviour and state that
    are extended by Leaders, Acceptors or Replicas.
    """ 
    def __init__(self,
                 nodetype,
                 addr=options.addr,
                 port=options.port,
                 givenbootstraplist=options.bootstrap,
                 debugoption=options.debug,
                 objectfilename=options.objectfilename,
                 objectname=options.objectname,
                 instantiateobj=False,
                 configpath=options.configpath,
                 logger=options.logger):
        self.addr = addr if addr else findOwnIP()
        self.port = port
        self.connectionpool = ConnectionPool()
        self.type = nodetype
        self.debug = debugoption
        if instantiateobj:
            if objectfilename == '':
                parser.print_help()
                self._graceexit(1)
            self.objectfilename = objectfilename
            self.objectname = objectname
        ## initialize receive queue
        self.receivedmessages_semaphore = Semaphore(0)
        self.receivedmessages = []
        # lock to synchronize message handling
        self.lock = Lock()
        # create server socket and bind to a port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket.setblocking(0)
        if self.port:
            try:
                self.socket.bind((self.addr,self.port))
            except socket.error:
                print "Cannot bind to port %d" % self.port
                self._graceexit(1)
        else:
            for i in range(50):
                self.port = random.randint(14000,15000)
                try:
                    self.socket.bind((self.addr,self.port))
                    break
                except socket.error:
                    pass
        self.socket.listen(10)
        self.alive = True
        # initialize empty groups
        self.me = Peer(self.addr,self.port,self.type)
        # set id
        self.id = getpeerid(self.me)
        # set path for additional configuration data
        self.configpath = configpath
        # set the logger
        try:
            LOGGERNODE = load_configdict(self.configpath)['LOGGERNODE']
        except:
            if logger:
                LOGGERNODE=logger
            else:
                LOGGERNODE = None
        if self.debug:
            self.logger = Logger("%s-%s" % (node_names[self.type],self.id), lognode=LOGGERNODE)
        else:
            self.logger = NoneLogger()
        self.logger.write("State", "Connected.")
        # Initialize groups
        # Keeps {peer:outofreachcount}
        self.replicas = {}
        self.acceptors = {}
        self.nameservers = {}
        self.groups = {NODE_REPLICA: self.replicas,
                       NODE_ACCEPTOR: self.acceptors,
                       NODE_NAMESERVER: self.nameservers}
        self.groups[self.me.type][self.me] = 0
        # connect to the bootstrap node
        if givenbootstraplist:
            self.bootstraplist = []
            self.discoverbootstrap(givenbootstraplist)
            self.connecttobootstrap()
        if self.type == NODE_REPLICA or self.type == NODE_NAMESERVER:
            self.stateuptodate = False

    def _getipportpairs(self, bootaddr, bootport):
        for node in socket.getaddrinfo(bootaddr, bootport):
            yield Peer(node[4][0],bootport,NODE_REPLICA)

    def discoverbootstrap(self, givenbootstraplist):
        bootstrapstrlist = givenbootstraplist.split(",")
        for bootstrap in bootstrapstrlist:
            #ipaddr:port pair given as bootstrap
            if bootstrap.find(":") >= 0:
                bootaddr,bootport = bootstrap.split(":")
                for peer in self._getipportpairs(bootaddr, int(bootport)):
                    self.bootstraplist.append(peer)
            #dnsname given as bootstrap
            else:
                answers = []
                try:
                    answers = dns.resolver.query('_concoord._tcp.'+bootstrap, 'SRV')
                except (dns.resolver.NXDOMAIN, dns.exception.Timeout):
                    self.logger.write("DNS Error", "Cannot resolve %s" % str(bootstrap))
                for rdata in answers:
                    for peer in self._getipportpairs(str(rdata.target), rdata.port):
                        self.bootstraplist.append(peer)

    def connecttobootstrap(self):
        tries = 0
        keeptrying = True
        while tries < BOOTSTRAPCONNECTTIMEOUT and keeptrying:
            for bootpeer in self.bootstraplist:
                try:
                    self.logger.write("State", "trying to connect to bootstrap: %s" % str(bootpeer))
                    helomessage = create_message(MSG_HELO, self.me)
                    success = self.send(helomessage, peer=bootpeer)
                    if success < 0:
                        tries += 1
                        continue
                    keeptrying = False
                    break
                except socket.error, e:
                    self.logger.write("Connection Error", "cannot connect to bootstrap: %s" % str(e))
                    print e
                    tries += 1
                    continue
            time.sleep(1)

    def startservice(self):
        # Start a thread that waits for inputs
        receiver_thread = Thread(target=self.server_loop, name='ReceiverThread')
        receiver_thread.start()
        # Start a thread with the server which will start a thread for each request
        main_thread = Thread(target=self.handle_messages, name='MainThread')
        main_thread.start()
        # Start a thread that waits for inputs
        input_thread = Thread(target=self.get_user_input_from_shell, name='InputThread')
        input_thread.start()
        # Start a thread that pings all neighbors
        ping_thread = Timer(LIVENESSTIMEOUT, self.ping_neighbor)
        ping_thread.name = 'PingThread'
        ping_thread.start()
        return self

    def ping_neighbor(self):
        """used to ping neighbors periodically"""
        while True:
            # Go through all peers in the view
            for gtype,group in self.groups.iteritems():
                for peer in group.iterkeys():
                    self.logger.write("State", "Sending PING to %s" % str(peer))
                    pingmessage = create_message(MSG_PING, self.me)
                    success = self.send(pingmessage, peer=peer)
                    if success < 0:
                        self.logger.write("State", "Neighbor not responding, marking the neighbor")
                        self.groups[peer.type][peer] += 1
                    else:
                        self.groups[peer.type][peer] = 0
            time.sleep(LIVENESSTIMEOUT)

    def __str__(self):
        return "%s NODE %s:%d" % (node_names[self.type], self.addr, self.port)

    def statestr(self):
        groups = "".join(str(group) for type,group in self.groups.iteritems())
        if hasattr(self,'pendingcommands') and len(self.pendingcommands) > 0:
            pending =  "".join("%d: %s" % (cno, proposal) for cno,proposal in self.pendingcommands.iteritems())
            groups = "%s\nPending:\n%s" % (groups, pending)
        return groups
    
    def server_loop(self):
        """Serverloop that listens to multiple connections and accepts new ones.

        Server State
        - nascentset: set of sockets on which a MSG_HELO has not been received yet
        - socketset: sockets the server waits on
        - inputready: sockets that are ready for reading
        - exceptready: sockets that are ready according to an *exceptional condition*
        """
        self.socket.listen(10)
        nascentset = []
        while self.alive:
            try:
                # collect the set of all sockets that we want to listen to
                socketset = [self.socket] # add the server socket
                # add sockets from connectionpool
                for conn in self.connectionpool.poolbypeer.itervalues():
                    sock = conn.thesocket
                    if sock is not None:
                        if sock not in socketset:
                            socketset.append(sock)
                # add clientsockets if they exist
                try:
                    for conn in self.clientpool.poolbypeer.itervalues():
                        sock = conn.thesocket
                        if sock is not None and sock not in socketset:
                            socketset.append(sock)
                except AttributeError:
                    pass
                
                # add sockets we didn't receive a message from yet, which are not expired
                for s,timestamp in nascentset:
                    # prune and close old sockets that never got turned into connections
                    if time.time() - timestamp > NASCENTTIMEOUT:
                        # expired -- if it's not already in the set, it should be closed
                        if s not in socketset:
                            nascentset.remove((s,timestamp))
                            s.close()
                    elif s not in socketset:
                        # check if it has been added before
                        socketset.append(s)

                assert len(socketset) == len(set(socketset)), "[%s] socketset has Duplicates." % self
                inputready,outputready,exceptready = select.select(socketset,[],socketset,1)
  
                for s in exceptready:
                    print "EXCEPTION ", s
                for s in inputready:
                    if s == self.socket:
                        clientsock,clientaddr = self.socket.accept()
                        self.logger.write("State", "accepted a connection from address %s" % str(clientaddr))
                        nascentset.append((clientsock,time.time()))
                        success = True
                    else:
                        success = self.handle_connection(s)
                    if not success:
                        # s is closed, take it out of nascentset and connection pool
                        for sock,timestamp in nascentset:
                            if sock == s:
                                nascentset.remove((sock,timestamp))
                        self.connectionpool.del_connection_by_socket(s)
                        s.close()
            except KeyboardInterrupt, EOFError:
                os._exit(0)
        self.socket.close()
        return
        
    def handle_connection(self, clientsock):
        """Receives a message and calls the corresponding message handler"""
        connection = self.connectionpool.get_connection_by_socket(clientsock)
        message = connection.receive()
        if message == None:
            return False
        else:
            self.logger.write("State", "received %s" % str(message))
            if message.type == MSG_STATUS:
                if self.type == NODE_REPLICA:
                    self.logger.write("State", "Answering status message %s" % self.__str__())
                    messagestr = pickle.dumps(self.__str__())
                    message = struct.pack("I", len(messagestr)) + messagestr
                    clientsock.send(message)
                return
            # add to receivedmessages
            self.receivedmessages.append((message,connection))
            self.receivedmessages_semaphore.release()
            if message.type == MSG_CLIENTREQUEST or message.type == MSG_INCCLIENTREQUEST:
                try:
                    self.clientpool.add_connection_to_peer(message.source, connection)
                except AttributeError:
                    pass
            else:
                self.connectionpool.add_connection_to_peer(message.source, connection)
        return True

    def handle_messages(self):
        while True:
            self.receivedmessages_semaphore.acquire()
            if self.type == NODE_REPLICA and len(self.pendingmetacommands) > 0:
                # A node should be removed from the view
                with self.pendingmetalock:
                    self.pendingmetacommands = set()
                self.initiate_command()
#            try:
            (message_to_process,connection) = self.receivedmessages.pop(0)
            if message_to_process.type == MSG_CLIENTREQUEST:
                # check if there are other client requests waiting
                msgconns = [(message_to_process,connection)]
                for m,c in self.receivedmessages:
                    if m.type == MSG_CLIENTREQUEST:
                        # decrement the semaphore count
                        self.receivedmessages_semaphore.acquire()
                        # remove the m,c pair from receivedmessages
                        self.receivedmessages.remove((m,c))
                        msgconns.append((m,c))
                if len(msgconns) > 1:
                    print "BATCHING NOW!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
                    self.process_messagelist(msgconns)
                else:
                    self.process_message(message_to_process, connection)
            else:
                self.process_message(message_to_process, connection)
#            except Exception as e:
#                continue
        return

    def process_messagelist(self, msgconnlist):
        """Processes given message connection pairs"""
        with self.lock:
            #XXX batched
            self.msg_clientrequest_batch(msgconnlist)
        return True

    def process_message(self, message, connection):
        """Processes given message connection pair"""
        # find method and invoke it holding a lock
        mname = "msg_%s" % msg_names[message.type].lower()
        try:
            method = getattr(self, mname)
            self.logger.write("State", "invoking method: %s" % mname)
        except AttributeError:
            self.logger.write("Method Error", "method not supported: %s" % mname)
            return False
        with self.lock:
            method(connection, message)
        return True

    # message handlers
    def msg_helo(self, conn, msg):
        return

    def msg_heloreply(self, conn, msg):
        if msg.leader:
            self.bootstraplist.remove(msg.source)
            self.bootstraplist.append(msg.leader)
            self.connecttobootstrap()
        else:
            self.groups[NODE_REPLICA].add(msg.source)
            self.logger.write("State", "connected to bootstrap: %s:%d" % (msg.source.addr,msg.source.port))

    def msg_ping(self, conn, msg):
        return

    def msg_bye(self, conn, msg):
        """Deletes the source of MSG_BYE from groups"""
        del self.groups[msg.source.type][msg.source]
        
    # shell commands generic to all nodes
    def cmd_help(self, args):
        """prints the commands that are supported
        by the corresponding Node.""" 
        print "Commands I support:"
        for attr in dir(self):
            if attr.startswith("cmd_"):
                print attr.replace("cmd_", "")

    def cmd_exit(self, args):
        """Changes the liveness state and send MSG_BYE to Peers.""" 
        self.alive = False
        byemessage = create_message(MSG_BYE, self.me)
        for type,nodegroup in self.groups.iteritems():
            self.send(byemessage, group=nodegroup)
        self.send(byemessage, peer=self.me)
        os._exit(0)
                    
    def cmd_state(self, args):
        """prints connectivity state of the corresponding Node."""
        self.logger.write("State", "\n%s\n" % (self.statestr()))

    def get_user_input_from_shell(self):
        """Shell loop that accepts inputs from the command prompt and 
        calls corresponding command handlers."""
        while self.alive:
            try:
                input = raw_input(">")
                if len(input) == 0:
                    continue
                else:
                    input = input.split()
                    mname = "cmd_%s" % input[0].lower()
                    try:
                        method = getattr(self, mname)
                    except AttributeError:
                        print "command not supported"
                        continue
                    with self.lock:
                        method(input)
            except (KeyboardInterrupt,):
                os._exit(0)
            except (EOFError,):
                return
        return           
    
    def send(self, message, peer=None, group=None, isresend=False):
        if peer:
            connection = self.connectionpool.get_connection_by_peer(peer)
            if connection == None:
                self.logger.write("Connection Error", "Connection for %s cannot be found." % str(peer))
                return -1
            connection.send(message)
            return message[FLD_ID]
        elif group:
            assert not isresend, "performing a re-send to a group"
            ids = []
            for peer in group.keys():
                if peer != self.me:
                    connection = self.connectionpool.get_connection_by_peer(peer)
                    if connection == None:
                        self.logger.write("Connection Error", "Connection for %s cannot be found." % str(peer))
                        continue
                    connection.send(message)
                    ids.append(message[FLD_ID])
                    message[FLD_ID] = assignuniqueid()
            return ids

    def terminate_handler(self, signal, frame):
        print self.me, "exiting.."
        self.logger.write("State", "exiting...")
        self.logger.close()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)

    def _graceexit(self, exitcode=0):
        sys.stdout.flush()
        sys.stderr.flush()
        print get_profile_stats()
        try:
            self.logger.close()
        except:
            pass
        os._exit(exitcode)
