'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Master class for all nodes
@copyright: See LICENSE
'''
import argparse
import os, sys
import random, struct
import cPickle as pickle
import time, socket, select
from Queue import Queue
from threading import Thread, RLock, Lock, Condition, Timer, Semaphore
from concoord.enums import *
from concoord.exception import ConnectionError
from concoord.utils import *
from concoord.message import *
from concoord.pack import *
from concoord.pvalue import PValueSet
from concoord.connection import ConnectionPool,Connection

try:
    import dns.resolver, dns.exception
except:
    print("Install dnspython: http://www.dnspython.org/")

parser = argparse.ArgumentParser()

parser.add_argument("-a", "--addr", action="store", dest="addr",
                    help="addr for the node")
parser.add_argument("-p", "--port", action="store", dest="port", type=int,
                    help="port for the node")
parser.add_argument("-b", "--boot", action="store", dest="bootstrap",
                    help="address:port tuple for the bootstrap peer")
parser.add_argument("-o", "--objectname", action="store", dest="objectname", default='',
                    help="client object dotted name")
parser.add_argument("-l", "--logger", action="store", dest="logger", default='',
                    help="logger address")
parser.add_argument("-c", "--configpath", action="store", dest="configpath", default='',
                    help="config file path")
parser.add_argument("-n", "--name", action="store", dest="domain", default='',
                    help="domainname that the nameserver will accept queries for")
parser.add_argument("-t", "--type", action="store", dest="type", default='',
                    help="1: Master Nameserver 2: Slave Nameserver (requires a Master) 3:Route53 (requires a Route53 zone)")
parser.add_argument("-m", "--master", action="store", dest="master", default='',
                    help="ipaddr:port for the master nameserver")
parser.add_argument("-w", "--writetodisk", action="store_true", dest="writetodisk", default=False,
                    help="writing to disk on/off")
parser.add_argument("-d", "--debug", action="store_true", dest="debug", default=False,
                    help="debug on/off")
args = parser.parse_args()

class Node():
    """Node encloses the basic Node behaviour and state that
    are extended by Leaders, Acceptors or Replicas.
    """
    def __init__(self,
                 nodetype,
                 addr=args.addr,
                 port=args.port,
                 givenbootstraplist=args.bootstrap,
                 debugoption=args.debug,
                 objectname=args.objectname,
                 instantiateobj=False,
                 configpath=args.configpath,
                 logger=args.logger,
                 writetodisk=args.writetodisk):
        self.addr = addr if addr else findOwnIP()
        self.port = port
        self.type = nodetype
        self.debug = debugoption
        self.durable = writetodisk
        if instantiateobj:
            if objectname == '':
                parser.print_help()
                self._graceexit(1)
            self.objectname = objectname
        # initialize receive queue
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
            except socket.error as e:
                print "Cannot bind to port %d" % self.port
                print "Socket Error: ", e
                self._graceexit(1)
        else:
            for i in range(50):
                self.port = random.randint(14000,15000)
                try:
                    self.socket.bind((self.addr,self.port))
                    break
                except socket.error as e:
                    print "Socket Error: ", e
                    pass
        self.socket.listen(10)
        self.connectionpool = ConnectionPool()
        try:
            self.connectionpool.epoll = select.epoll()
        except AttributeError as e:
            # the os doesn't support epoll
            self.connectionpool.epoll = None
        self.alive = True
        self.me = Peer(self.addr,self.port,self.type)
        # set id
        self.id = '%s:%d' % (self.addr, self.port)

        # set path for additional configuration data
        self.configpath = configpath
        # set the logger
        try:
            LOGGERNODE = load_configdict(self.configpath)['LOGGERNODE']
        except KeyError as e:
            if logger:
                LOGGERNODE=logger
            else:
                LOGGERNODE = None
        self.logger = Logger("%s-%s" % (node_names[self.type],self.id), lognode=LOGGERNODE)
        print "%s-%s connected." % (node_names[self.type],self.id)
        # Initialize groups
        # Keeps {peer:outofreachcount}
        self.replicas = {}
        self.acceptors = {}
        self.nameservers = {}
        self.groups = {NODE_REPLICA: self.replicas,
                       NODE_ACCEPTOR: self.acceptors,
                       NODE_NAMESERVER: self.nameservers}
        self.groups[self.me.type][self.me] = 0

        # Keeps the liveness of the nodes
        self.nodeliveness = {}
        # connect to the bootstrap node
        if givenbootstraplist:
            self.bootstraplist = []
            self.discoverbootstrap(givenbootstraplist)
            self.connecttobootstrap()
        if self.type == NODE_REPLICA or self.type == NODE_NAMESERVER:
            self.stateuptodate = False

    def _getipportpairs(self, bootaddr, bootport):
        for node in socket.getaddrinfo(bootaddr, bootport, socket.AF_INET, socket.SOCK_STREAM):
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
                    if self.debug: self.logger.write("DNS Error", "Cannot resolve %s" % str(bootstrap))
                for rdata in answers:
                    for peer in self._getipportpairs(str(rdata.target), rdata.port):
                        self.bootstraplist.append(peer)

    def connecttobootstrap(self):
        tries = 0
        keeptrying = True
        while tries < BOOTSTRAPCONNECTTIMEOUT and keeptrying:
            for bootpeer in self.bootstraplist:
                try:
                    if self.debug: self.logger.write("State",
                                                     "trying to connect to bootstrap: %s" % str(bootpeer))
                    helomessage = create_message(MSG_HELO, self.me)
                    successid = self.send(helomessage, peer=bootpeer)
                    if successid < 0:
                        tries += 1
                        continue
                    keeptrying = False
                    break
                except socket.error as e:
                    if self.debug: self.logger.write("Socket Error",
                                                     "cannot connect to bootstrap: %s" % str(e))
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
        # Start a thread that pings all neighbors
        ping_thread = Timer(LIVENESSTIMEOUT, self.ping_neighbor)
        ping_thread.name = 'PingThread'
        ping_thread.start()
        # Start a thread that goes through the nascentset and cleans expired ones
        nascent_thread = Timer(NASCENTTIMEOUT, self.clean_nascent)
        nascent_thread.name = 'NascentThread'
        nascent_thread.start()
        # Start a thread that waits for inputs
        if self.debug:
            input_thread = Thread(target=self.get_user_input_from_shell, name='InputThread')
            input_thread.start()
        return self

    def __str__(self):
        return "%s NODE %s:%d" % (node_names[self.type], self.addr, self.port)

    def statestr(self):
        returnstr = ""
        for type,group in self.groups.iteritems():
            for peer in group.iterkeys():
                returnstr += node_names[type] + " %s:%d\n" % (peer.addr,peer.port)
        if hasattr(self, 'pendingcommands') and len(self.pendingcommands) > 0:
            pending =  "".join("%d: %s" % (cno, proposal) for cno,proposal in self.pendingcommands.iteritems())
            returnstr = "%s\nPending:\n%s" % (returnstr, pending)
        return returnstr

    def ping_neighbor(self):
        """used to ping neighbors periodically"""
        # Only ping neighbors that didn't send a message in less than
        # LIVENESSTIMEOUT
        while True:
            # Check nodeliveness
            for gtype,group in self.groups.iteritems():
                for peer in group:
                    if peer == self.me:
                        continue
                    if peer in self.nodeliveness:
                        nosound = time.time() - self.nodeliveness[peer]
                    else:
                        # This node never sent a message, we should ping it
                        if self.debug: self.logger.write("State", "Sending PING to %s" % str(peer))
                        pingmessage = create_message(MSG_PING, self.me)
                        self.send(pingmessage, peer=peer)
                        continue

                    if (4*LIVENESSTIMEOUT) > nosound and nosound > LIVENESSTIMEOUT:
                        # Send PING to node
                        if self.debug: self.logger.write("State", "Sending PING to %s" % str(peer))
                        pingmessage = create_message(MSG_PING, self.me)
                        self.send(pingmessage, peer=peer)
                    elif nosound > (4*LIVENESSTIMEOUT):
                        # Neighbor not responding, mark the neighbor
                        if self.debug: self.logger.write("State",
                                                         "Neighbor not responding")
                        self.groups[peer.type][peer] += 1
            time.sleep(LIVENESSTIMEOUT)

    def clean_nascent(self):
        lastnascentset = set([])
        while True:
            for sock in lastnascentset.intersection(self.connectionpool.nascentsockets):
                # expired -- if it's not already in the set, it should be deleted
                self.connectionpool.activesockets.remove(sock)
                self.connectionpool.nascentsockets.remove(sock)
                lastnascentset = self.connectionpool.nascentsockets
            time.sleep(NASCENTTIMEOUT)

    def server_loop(self):
        """Serverloop that listens to multiple connections and accepts new ones.

        Server State
        - inputready: sockets that are ready for reading
        - exceptready: sockets that are ready according to an *exceptional condition*
        """
        self.socket.listen(10)

        if self.connectionpool.epoll:
            self.connectionpool.epoll.register(self.socket.fileno(), select.EPOLLIN)
            self.use_epoll()
        else:
            # the OS doesn't support epoll
            self.connectionpool.activesockets.add(self.socket)
            self.use_select()

        self.socket.close()
        return

    def use_epoll(self):
        while self.alive:
            try:
                events = self.connectionpool.epoll.poll(1)
                for fileno, event in events:
                    if fileno == self.socket.fileno():
                        clientsock, clientaddr = self.socket.accept()
                        clientsock.setblocking(0)
                        self.connectionpool.epoll.register(clientsock.fileno(), select.EPOLLIN)
                        self.connectionpool.epollsockets[clientsock.fileno()] = clientsock
                    elif event & select.EPOLLIN:
                        success = self.handle_connection(self.connectionpool.epollsockets[fileno])
                        if not success:
                            self.connectionpool.epoll.unregister(fileno)
                            self.connectionpool.del_connection_by_socket(self.connectionpool.epollsockets[fileno])
                            self.connectionpool.epollsockets[fileno].close()
                            del self.connectionpool.epollsockets[fileno]
                    elif event & select.EPOLLHUP:
                        self.connectionpool.epoll.unregister(fileno)
                        self.connectionpool.epollsockets[fileno].close()
                        del self.connectionpool.epollsockets[fileno]
            except KeyboardInterrupt, EOFError:
                os._exit(0)
        self.connectionpool.epoll.unregister(self.socket.fileno())
        self.connectionpool.epoll.close()

    def use_select(self):
        while self.alive:
            try:
                inputready,outputready,exceptready = select.select(self.connectionpool.activesockets,
                                                                   [],
                                                                   self.connectionpool.activesockets,
                                                                   1)

                for s in exceptready:
                    if self.debug: self.logger.write("Exception", "%s" % s)
                for s in inputready:
                    if s == self.socket:
                        clientsock,clientaddr = self.socket.accept()
                        if self.debug: self.logger.write("State",
                                                         "accepted a connection from address %s" 
                                                         % str(clientaddr))
                        self.connectionpool.activesockets.add(clientsock)
                        self.connectionpool.nascentsockets.add(clientsock)
                        success = True
                    else:
                        success = self.handle_connection(s)
                    if not success:
                        self.connectionpool.del_connection_by_socket(s)
            except KeyboardInterrupt, EOFError:
                os._exit(0)

    def handle_connection(self, clientsock):
        """Receives a message and calls the corresponding message handler"""
        connection = self.connectionpool.get_connection_by_socket(clientsock)
        try:
            for message in connection.received_bytes():
                if self.debug: self.logger.write("State", "received %s" % str(message))
                # Update self.nodeliveness
                self.nodeliveness[message.source] = time.time()
                if message.type == MSG_STATUS:
                    if self.type == NODE_REPLICA:
                        if self.debug: self.logger.write("State",
                                                         "Answering status message %s" 
                                                         % self.__str__())
                        messagestr = pickle.dumps(self.__str__())
                        message = struct.pack("I", len(messagestr)) + messagestr
                        clientsock.send(message)
                        return False
                # add to receivedmessages
                self.receivedmessages.append((message,connection))
                self.receivedmessages_semaphore.release()
                if message.type == MSG_CLIENTREQUEST or message.type == MSG_INCCLIENTREQUEST:
                    self.connectionpool.add_connection_to_peer(message.source, connection)
                elif message.type in (MSG_HELO, MSG_HELOREPLY, MSG_UPDATE):
                    self.connectionpool.add_connection_to_peer(message.source, connection)
            return True
        except ConnectionError as e:
            return False

    def handle_messages(self):
        while True:
            self.receivedmessages_semaphore.acquire()
            (message_to_process,connection) = self.receivedmessages.pop(0)
            if message_to_process.type == MSG_CLIENTREQUEST:
                if message_to_process.clientbatch:
                    self.process_message(message_to_process, connection)
                    continue
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
                    self.process_messagelist(msgconns)
                else:
                    self.process_message(message_to_process, connection)
            else:
                self.process_message(message_to_process, connection)
        return

    def process_messagelist(self, msgconnlist):
        """Processes given message connection pairs"""
        with self.lock:
            self.msg_clientrequest_batch(msgconnlist)
        return True

    def process_message(self, message, connection):
        """Processes given message connection pair"""
        # find method and invoke it holding a lock
        mname = "msg_%s" % msg_names[message.type].lower()
        try:
            method = getattr(self, mname)
            if self.debug: self.logger.write("State", "invoking method: %s" % mname)
        except AttributeError:
            if self.debug: self.logger.write("Method Error", "method not supported: %s" % mname)
            return False
        with self.lock:
            method(connection, message)
        return True

    # message handlers
    def msg_helo(self, conn, msg):
        return

    def msg_heloreply(self, conn, msg):
        if msg.leader:
            if msg.source == msg.leader:
                if self.debug: self.logger.write("Error", "There are no acceptors yet, waiting.")
                # If heloreply received, should ping the bootstrap again to try connecting.
                time.sleep(1)
                self.connecttobootstrap()
                return
            elif msg.leader == self.me:
                if self.debug: self.logger.write("State", "I'm the leader.")
                return
            else:
                if self.debug: self.logger.write("State", "Adding new bootstrap.")
                self.bootstraplist.remove(msg.source)
                self.bootstraplist.append(msg.leader)
                self.connecttobootstrap()

    def msg_ping(self, conn, msg):
        if self.debug: self.logger.write("State", "Replying to PING.")
        pingreplymessage = create_message(MSG_PINGREPLY, self.me)
        conn.send(pingreplymessage)

    def msg_pingreply(self, conn, msg):
        return

    # shell commands generic to all nodes
    def cmd_help(self, args):
        """prints the commands that are supported
        by the corresponding Node."""
        print "Commands supported:"
        for attr in dir(self):
            if attr.startswith("cmd_"):
                print attr.replace("cmd_", "")

    def cmd_exit(self, args):
        """Changes the liveness state and dies"""
        self.alive = False
        os._exit(0)

    def cmd_state(self, args):
        """prints connectivity state of the corresponding Node."""
        print "\n%s\n" % (self.statestr())

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
                    except AttributeError as e:
                        print "Command not supported: ", str(e)
                        continue
                    with self.lock:
                        method(input)
            except KeyboardInterrupt:
                os._exit(0)
            except EOFError:
                return
        return

    def send(self, message, peer=None, group=None):
        if peer:
            connection = self.connectionpool.get_connection_by_peer(peer)
            if connection == None:
                if self.debug: self.logger.write("Connection Error",
                                                 "Connection for %s cannot be found." % str(peer))
                return -1
            connection.send(message)
            return message[FLD_ID]
        elif group:
            ids = []
            for peer,liveness in group.iteritems():
                if peer != self.me and liveness == 0:
                    connection = self.connectionpool.get_connection_by_peer(peer)
                    if connection == None:
                        if self.debug: self.logger.write("Connection Error",
                                                         "Connection for %s cannot be found." % str(peer))
                        continue
                    connection.send(message)
                    ids.append(message[FLD_ID])
                    message[FLD_ID] = assignuniqueid()
            return ids

    def terminate_handler(self, signal, frame):
        if self.debug: self.logger.write("State", "exiting...")
        self.logger.close()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)

    def _graceexit(self, exitcode=0):
        sys.stdout.flush()
        sys.stderr.flush()
        if hasattr(self, 'logger'): self.logger.close()
        os._exit(exitcode)
