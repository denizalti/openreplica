'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Master class for all nodes
@date: February 1, 2011
@copyright: See LICENSE
'''
from optparse import OptionParser
from threading import Thread, RLock, Lock, Condition, Timer, Semaphore
from Queue import Queue
import time
import socket, select
import os, sys
import random, struct
import cPickle as pickle
import copy
from connection import ConnectionPool,Connection
from group import Group
from peer import Peer
from command import Command
from pvalue import PValue, PValueSet
from enums import *
from utils import *
from message import *
try:
    from openreplicasecret import LOGGERNODE
except:
    print "To turn on Logging through the Network, edit NetworkLogger credentials"
    LOGGERNODE = 'addr:12000'
try:
    import dns.resolver, dns.exception
except:
    print("Install dnspython: http://www.dnspython.org/")

parser = OptionParser(usage="usage: %prog -a addr -p port -b bootstrap -f objectfilename -c objectname -n subdomainname -d debug")
parser.add_option("-a", "--addr", action="store", dest="addr", help="addr for the node")
parser.add_option("-p", "--port", action="store", dest="port", type="int", help="port for the node")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port:type triple for the bootstrap peer")
parser.add_option("-f", "--objectfilename", action="store", dest="objectfilename", default='', help="client object file name")
parser.add_option("-c", "--objectname", action="store", dest="objectname", help="object name")
parser.add_option("-n", "--name", action="store", dest="dnsname", default='', help="dns name")
parser.add_option("-d", "--debug", action="store_true", dest="debug", default=False, help="debug on/off")

(options, args) = parser.parse_args()

DO_PERIODIC_PINGS = False
RESEND = False

class Node():
    """Node encloses the basic Node behaviour and state that
    are extended by Leaders, Acceptors or Replicas.
    """ 
    def __init__(self, nodetype, addr=options.addr, port=options.port, givenbootstraplist=options.bootstrap, debugoption=options.debug, objectfilename=options.objectfilename, objectname=options.objectname, dnsname=options.dnsname, instantiateobj=False):
        """Node State
        - addr: hostname for Node, detected automatically
        - port: port for Node, can be taken from the commandline (-p [port]) or
        detected automatically by binding.
        - connectionpool: ConnectionPool that keeps all Connections Node knows about
        - type: type of the corresponding Node: NODE_ACCEPTOR | NODE_REPLICA | NODE_NAMESERVER
        - alive: liveness of Node
        - outstandingmessages: collection of sent but not-yet-acked messages
        - socket: server socket for Node
        - me: Peer object that represents Node
        - id: id for Node (addr:port)
        - groups: other Peers in the system that Node knows about. Node.groups is indexed by the
        corresponding node_name (NODE_ACCEPTOR | NODE_REPLICA | NODE_NAMESERVER), which returns a Group
        """
        self.addr = addr if addr else findOwnIP()
        self.port = port
        self.connectionpool = ConnectionPool()
        self.type = nodetype
        if instantiateobj:
            if objectfilename == '':
                parser.print_help()
                self._graceexit(1)
            self.objectfilename = objectfilename
            self.objectname = objectname

        ## messaging layer information
        self.receivedmessages_semaphore = Semaphore(0)
        self.receivedmessages = []
        # msgs not acked yet
        # {msgid: msginfo}
        self.outstandingmessages_lock =RLock()
        self.outstandingmessages = {}
        # last msg timestamp for all peers
        # {peer: timestamp}
        self.lastmessages_lock =RLock()
        self.lastmessages = {}
        # number of retries for all peers
        # {peer: retries}
        self.retries_lock =RLock()
        self.retries = {}
        
        self.lock = Lock()
        self.done = False
        self.donecond = Condition()

        # create server socket and bind to a port
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.socket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        self.socket.setblocking(0)
        if self.port:
            try:
                self.socket.bind((self.addr,self.port))
            except socket.error:
                print "Cannot bind to port %d" % self.port
                self._graceexit(1)
        else:
            self.port = random.randint(14000,15000)
            for i in range(50):
                try:
                    self.socket.bind((self.addr,self.port))
                    break
                except socket.error:
                    pass
        self.socket.listen(10)
        self.alive = True
        
        # initialize empty groups
        self.me = Peer(self.addr,self.port,self.type)
        self.id = self.me.getid()
        self.logger = NetworkLogger("%s-%s" % (node_names[self.type],self.id), LOGGERNODE)
        self.logger.write("State", "Connected.")
        self.groups = {NODE_ACCEPTOR:Group(self.me), NODE_REPLICA: Group(self.me), NODE_NAMESERVER:Group(self.me)}
        # connect to the bootstrap node
        if givenbootstraplist:
            self.bootstraplist = []
            self.discoverbootstrap(givenbootstraplist)
            self.connecttobootstrap()
        if self.type == NODE_REPLICA or self.type == NODE_NAMESERVER:
            self.stateuptodate = False

    def createinfofile(self):
        try:
            infofile = open(self.objectfilename[:-3]+"-descriptor", 'a')
            infofile.write("%s:%d" %(self.addr,self.port))
            infofile.close()
        except IOError as e:
            self.logger.write("File Error", "Info file cannot be created.")
            self._graceexit(1)

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
                    self.logger.write("DNS Error", "Cannot resolve %s" % bootstrap)
                for rdata in answers:
                    for peer in self._getipportpairs(str(rdata.target), rdata.port):
                        self.bootstraplist.append(peer)

    def connecttobootstrap(self):
        tries = 0
        keeptrying = True
        while tries < BOOTSTRAPCONNECTTIMEOUT and keeptrying:
            for bootpeer in self.bootstraplist:
                try:
                    self.logger.write("State", "trying to connect to bootstrap: %s" % bootpeer)
                    helomessage = HandshakeMessage(MSG_HELO, self.me)
                    success = self.send(helomessage, peer=bootpeer)
                    if success < 0:
                        tries += 1
                        continue
                    self.groups[NODE_REPLICA].add(bootpeer)
                    self.logger.write("State", "connected to bootstrap: %s:%d" % (bootpeer.addr,bootpeer.port))
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
        # Start a thread that pings neighbors
        timer_thread = Timer(ACKTIMEOUT/5, self.periodic)
        timer_thread.name = 'PeriodicThread'
        timer_thread.start()
        return self

    def __str__(self):
        return "%s NODE %s:%d" % (node_names[self.type], self.addr, self.port)

    def statestr(self):
        groups = "".join(str(group) for type,group in self.groups.iteritems())
        if hasattr(self,'pendingcommands') and len(self.pendingcommands) > 0:
            pending =  "".join("%d: %s" % (cno, proposal) for cno,proposal in self.pendingcommands.iteritems())
            groups = "%s\nPending:\n%s" % (groups, pending)
        return groups

    def outstandingmsgstr(self):
        returnstr = "outstandingmessages: time now is %s\n" % str(time.time())
        with self.outstandingmessages_lock:
            for messageid,messageinfo in self.outstandingmessages.iteritems():
                returnstr += "[%s] %s\n" % (str(messageid),str(messageinfo))
        return returnstr
    
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
        timestamp,message = connection.receive()
        if message == None:
            return False
        else:
            self.logger.write("State", "received %s" % message)
            if message.type == MSG_STATUS:
                if self.type == NODE_REPLICA:
                    self.logger.write("State", "Answering status message %s" % self.__str__())
                    messagestr = pickle.dumps(self.__str__())
                    message = struct.pack("I", len(messagestr)) + messagestr
                    clientsock.send(message)
                return
            # add to lastmessages
            with self.lastmessages_lock:
                if not self.lastmessages.has_key(message.source):
                    self.lastmessages[message.source] = timestamp
                elif self.lastmessages[message.source] < timestamp:
                    self.lastmessages[message.source] = timestamp
            # add to receivedmessages
            self.receivedmessages.append((timestamp,message,connection))
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
            (timestamp, message_to_process, connection) = self.receivedmessages.pop(0)
            self.process_message(message_to_process, connection)
        return

    def process_message(self, message, connection):
        """Process message loop that takes messages out of the receivedmessages
        list and handles them.
        """
        # check to see if it's an ack
        if message.type == MSG_ACK:
            #take it out of outstanding messages, but do not ack an ack
            ackid = "%s+%d" % (self.id, message.ackid)
            with self.outstandingmessages_lock:
                if self.outstandingmessages.has_key(ackid):
                    del self.outstandingmessages[ackid]
            return True
        elif message.type != MSG_CLIENTREQUEST and message.type != MSG_INCCLIENTREQUEST:
            # Send ACK
            connection.send(AckMessage(MSG_ACK,self.me,message.id))
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

    #
    # message handlers
    #
    def msg_helo(self, conn, msg):
        return

    def msg_heloreply(self, conn, msg):
        if msg.reject:
            self.connecttobootstrap()

    def msg_ping(self, conn, msg):
        return

    def msg_refer(self, conn, msg):
        self.logger.write("Message Error", "Received a REFER message, not a coordinator.")

    def msg_bye(self, conn, msg):
        """Deletes the source of MSG_BYE from groups"""
        self.groups[msg.source.type].remove(msg.source)
        
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
        byemessage = Message(MSG_BYE,self.me)
        for type,nodegroup in self.groups.iteritems():
            self.send(byemessage, group=nodegroup)
        self.send(byemessage, peer=self.me)
        os._exit(0)
                    
    def cmd_state(self, args):
        """prints connectivity state of the corresponding Node."""
        self.logger.write("State", "\n%s\n%s\n" % (self.statestr(), self.outstandingmsgstr()))

    def periodic(self):
        """timer function that is responsible for periodic state maintenance
        - resends messages that are in outstandingmessages and are older than ACKTIMEOUT.
        - sends MSG_HELO message to peers that it has not heard within LIVENESSTIMEOUT
        """
        while True:
            if DO_PERIODIC_PINGS:
                checkliveness = set()
                for type,group in self.groups.iteritems():
                    checkliveness = checkliveness.union(group.members)
            if RESEND:
                try:
                    with self.outstandingmessages_lock:
                        msgs = self.outstandingmessages.values()
                    for messageinfo in msgs:
                        now = time.time()
                        if messageinfo.timestamp + ACKTIMEOUT < now:
                            if messageinfo.message.type != MSG_PING:
                                self.logger.write("State", "re-sending to %s, message %s" % (messageinfo.destination, messageinfo.message))
                                self.send(messageinfo.message, peer=messageinfo.destination, isresend=True)
                                self.add_retry(messageinfo.destination)
                                messageinfo.timestamp = time.time()
                        elif DO_PERIODIC_PINGS and (messageinfo.timestamp + LIVENESSTIMEOUT) < now and messageinfo.destination in checkliveness:
                            checkliveness.remove(messageinfo.destination)
                except Exception as e:
                    self.logger.write("Connection Error", "exception in resend: %s" % e)
            if DO_PERIODIC_PINGS:
                for pingpeer in checkliveness:
                    # don't ping the peer if it has sent a message recently
                    if self.lastmessages[pingpeer] + LIVENESSTIMEOUT >= now:
                        self.logger.write("State", "sending PING to %s" % pingpeer)
                        pingmessage = HandshakeMessage(MSG_PING, self.me)
                        self.send(pingmessage, peer=pingpeer)
            time.sleep(ACKTIMEOUT)

    def add_retry(self, peer):
        with self.retries_lock:
            if self.retries.has_key(peer):
                self.retries[peer] += 1
            else:
                self.retries[peer] = 1

    def get_user_input_from_shell(self):
        """Shell loop that accepts inputs from the command prompt and 
        calls corresponding command handlers.
        """
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
            if not isresend:
                msginfo = MessageInfo(message,peer,time.time())
                with self.outstandingmessages_lock:
                    self.outstandingmessages[message.fullid()] = msginfo
            connection.send(message)
            return message.id
        elif group:
            assert not isresend, "performing a re-send to a group"
            ids = []
            for peer in group.members:
                connection = self.connectionpool.get_connection_by_peer(peer)
                if connection == None:
                    self.logger.write("Connection Error", "Connection for %s cannot be found." % str(peer))
                    continue
                msginfo = MessageInfo(message,peer,time.time())
                with self.outstandingmessages_lock:
                    self.outstandingmessages[message.fullid()] = msginfo
                connection.send(message)
                ids.append(message.id)
                message = copy.copy(message)
                message.assignuniqueid()
            return ids

    def terminate_handler(self, signal, frame):
        print self.me, "exiting.."
        self.logger.write("State", "exiting...")
        self.logger.close()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)
