'''
@author: egs
@note: Master class for all nodes
@date: February 1, 2011
'''
from optparse import OptionParser
from threading import Thread, RLock, Lock, Condition, Timer, Semaphore
from time import sleep,time
from Queue import Queue
import socket
import os
import sys
import time
import random
import select
import copy
import fcntl
try:
    import dns.resolver
except:
    logger("Install dnspython: http://www.dnspython.org/")

from enums import *
from utils import *
from connection import ConnectionPool,Connection
from group import Group
from peer import Peer
from message import *
from command import Command
from pvalue import PValue, PValueSet
from concoordprofiler import *

parser = OptionParser(usage="usage: %prog -p port -b bootstrap -o object -l -d")
parser.add_option("-p", "--port", action="store", dest="port", type="int", default=6668, help="port for the node")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port:type triple for the bootstrap peer")
parser.add_option("-o", "--object", action="store", dest="object", default=None, help="replicated object")
parser.add_option("-l", "--local", action="store_true", dest="local", default=False, help="initiates the node at localhost")
parser.add_option("-d", "--debug", action="store_true", dest="debug", default=False, help="debug on/off")
parser.add_option("-n", "--name", action="store", dest="dnsname", default='', help="dns name")

(options, args) = parser.parse_args()

DO_PERIODIC_PINGS = False

class Node():
    """Node encloses the basic Node behaviour and state that
    are extended by Leaders, Acceptors or Replicas.
    """ 
    def __init__(self, nodetype, port=options.port, givenbootstraplist=options.bootstrap, local=options.local, debugoption=options.debug, replicatedobject=options.object, dnsname=options.dnsname, instantiateobj=False):
        """Node State
        - addr: hostname for Node, detected automatically
        - port: port for Node, can be taken from the commandline (-p [port]) or
        detected automatically by binding.
        - connectionpool: ConnectionPool that keeps all Connections Node knows about
        - type: type of the corresponding Node: NODE_LEADER | NODE_ACCEPTOR | NODE_REPLICA
        - alive: liveness of Node
        - outstandingmessages: keeps <messageid:messageinfo> mappings as <MessageID:MessageInfo> objects
        - socket: socket of Node
        - me: Peer object that represents Node
        - id: id for Node (addr:port)
        - groups: other Peers in the system that Node knows about. Node.groups is indexed by the
        corresponding node_name (NODE_LEADER | NODE_ACCEPTOR | NODE_REPLICA | NODE_NAMESERVER), which returns a Group
        """
        if local == True:
            self.addr = '127.0.0.1'
        else:
            self.addr = findOwnIP() 
        self.port = port
        self.connectionpool = ConnectionPool()
        self.type = nodetype
        if instantiateobj:
            self.objectfilename, self.objectname = replicatedobject.split(".")

        self.receivedmessages_semaphore = Semaphore(0)
        self.receivedmessages = []
        
        self.outstandingmessages_lock =RLock()
        self.outstandingmessages = {}
        
        self.lock = Lock()
        self.done = False
        self.donecond = Condition()

        # create server socket and bind to a port
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.socket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        self.socket.setblocking(0)
        for i in range(30):
            try:
                self.socket.bind((self.addr,self.port))
                break
            except socket.error:
                self.port += 1
        self.socket.listen(10)
        self.alive = True
        
        # initialize empty groups
        self.me = Peer(self.addr,self.port,self.type)
        self.id = self.me.getid()
        if debugoption:
            setlogprefix("%s %s" % (node_names[self.type],self.id))
        self.groups = {NODE_ACCEPTOR:Group(self.me), NODE_REPLICA: Group(self.me), NODE_LEADER:Group(self.me), \
                       NODE_TRACKER:Group(self.me), NODE_COORDINATOR:Group(self.me), NODE_NAMESERVER:Group(self.me)}
        # connect to the bootstrap node
        if givenbootstraplist:
            self.bootstraplist = []
            self.discoverbootstrap(givenbootstraplist)
            self.connecttobootstrap()
            
        if self.type == NODE_REPLICA or self.type == NODE_TRACKER or self.type == NODE_NAMESERVER or self.type == NODE_COORDINATOR:
            self.stateuptodate = False
        print self.id

    def _getipportpairs(self, bootaddr, bootport):
        for node in socket.getaddrinfo(bootaddr, bootport):
            yield Peer(node[4][0],bootport,NODE_REPLICA)

    def discoverbootstrap(self, givenbootstraplist):
        bootstrapstrlist = givenbootstraplist.split(",")
        for bootstrap in bootstrapstrlist:
            if bootstrap.find(":") >= 0:
                bootaddr,bootport = bootstrap.split(":")
                for peer in self._getipportpairs(bootaddr, int(bootport)):
                    self.bootstraplist.append(peer)
            else:
                answers = dns.resolver.query('_concoord._tcp.'+bootstrap, 'SRV')
                for rdata in answers:
                    for peer in self._getipportpairs(str(rdata.target), rdata.port):
                        self.bootstraplist.append(peer)

    def connecttobootstrap(self):
        for bootpeer in self.bootstraplist:
            try:
                logger("trying to connect to bootstrap: %s" % bootpeer)
                helomessage = HandshakeMessage(MSG_HELO, self.me)
                self.send(helomessage, peer=bootpeer)
                self.groups[NODE_REPLICA].add(bootpeer)
                logger("connected to bootstrap: %s:%d" % (bootpeer.addr,bootpeer.port))
                break
            except socket.error, e:
                print e
                continue

    def startservice(self):
        """Starts the background services associated with a node."""
        # Start a thread that waits for inputs
        receiver_thread = Thread(target=self.server_loop)
        receiver_thread.start()
        # Start a thread with the server which will start a thread for each request
        main_thread = Thread(target=self.handle_messages)
        main_thread.start()
        # Start a thread that waits for inputs
        input_thread = Thread(target=self.get_inputs)
        input_thread.start()
        # Start a thread that pings neighbors
        timer_thread = Timer(ACKTIMEOUT/5, self.periodic)
        timer_thread.start()

    def signalend(self):
        with self.donecond:
            self.done = True
            self.donecond.notifyAll()
            
    def waituntilend(self):
        with self.donecond:
            while self.done == False:
                self.donecond.wait()
        logger("End of life")

    def __str__(self):
        """Return Node information (addr:port)"""
        return "%s  %s:%d" % (node_names[self.type], self.addr, self.port)

    def statestr(self):
        """Return the Peers Node knows of, i.e. connectivity state"""
        groups = "".join(str(group) for type,group in self.groups.iteritems())
        if hasattr(self,'pendingcommands') and len(self.pendingcommands) > 0:
            pending =  "".join("%d: %s" % (cno, proposal) for cno,proposal in self.pendingcommands.iteritems())
            groups = "%s\nPending:\n%s" % (groups, pending)
        return groups

    def outstandingmsgstr(self):
        """Return the dictionary of outstandingmessages"""
        returnstr = "outstandingmessages: time now is %s\n" % str(time.time())
        with self.outstandingmessages_lock:
            for messageid,messageinfo in self.outstandingmessages.iteritems():
                returnstr += "[%s] %s\n" % (str(messageid),str(messageinfo))
        return returnstr
    
    def server_loop(self):
        """Serverloop that listens to multiple sockets and accepts connections.

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
                        logger("accepted a connection from address %s" % str(clientaddr))
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
            # Add to received messages
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
        """Process message loop that takes messages out of the receives_messages
        list and handles them.
        """
        # check to see if it's an ack
        if message.type == MSG_ACK:
            #take it out of outstanding messages, but do not ack an ack
            ackid = "%s+%d" % (self.me.getid(), message.ackid)
            with self.outstandingmessages_lock:
                if self.outstandingmessages.has_key(ackid):
                    del self.outstandingmessages[ackid]
            return True
        elif message.type != MSG_CLIENTREQUEST and message.type != MSG_INCCLIENTREQUEST:
            # Send ACK
            connection.send(AckMessage(MSG_ACK,self.me,message.id))
        mname = "msg_%s" % msg_names[message.type].lower()
        try:
            method = getattr(self, mname)
        except AttributeError:
            logger("message not supported: %s" % message)
            return False
        with self.lock:
            method(connection, message)
        return True
    
    #
    # message handlers
    #
    def msg_helo(self, conn, msg):
        if len(self.groups[NODE_COORDINATOR]) > 0:
            refermessage = ReferMessage(MSG_REFER, self.me, referredpeer=msg.source)
            self.send(refermessage, group=self.groups[NODE_COORDINATOR])
        else:
            return

    def msg_heloreply(self, conn, msg):
        for nodetype in msg.groups.keys():
            for node in msg.groups[nodetype]:
                self.groups[nodetype].add(node)

    def msg_ping(self, conn, msg):
        return

    def msg_refer(self, conn, msg):
        logger("Received a REFER message, not a coordinator.")

    def msg_bye(self, conn, msg):
        """Deletes the source of MSG_BYE from groups"""
        self.groups[msg.source.type].remove(msg.source)
        
    # shell commands generic to all nodes
    def cmd_help(self, args):
        """Shell command [help]: Prints the commands that are supported
        by the corresponding Node.""" 
        print "Commands I support:"
        for attr in dir(self):
            if attr.startswith("cmd_"):
                print attr.replace("cmd_", "")

    def cmd_exit(self, args):
        """Shell command [exit]: Changes the liveness state and send MSG_BYE to Peers.""" 
        self.alive = False
        byemessage = Message(MSG_BYE,self.me)
        for type,nodegroup in self.groups.iteritems():
            self.send(byemessage, group=nodegroup)
        self.send(byemessage, peer=self.me)
        os._exit(0)
                    
    def cmd_state(self, args):
        """Shell command [state]: Prints connectivity state of the corresponding Node."""
        logger("\n%s\n%s\n" % (self.statestr(), self.outstandingmsgstr()))

    def periodic(self):
        """timer function that is responsible for periodic state maintenance
        
        - goes through outstanding messages and resends messages that are older than
          ACKTIMEOUT and are NOTACKED yet.
        - sends MSG_HELO message to peers that it has not heard within LIVENESSTIMEOUT
        """
        while True:
            if DO_PERIODIC_PINGS:
                checkliveness = set()
                for type,group in self.groups.iteritems():
                    checkliveness = checkliveness.union(group.members)

            try:
                with self.outstandingmessages_lock:
                    msgs = self.outstandingmessages.values()
                for messageinfo in msgs:
                    now = time.time()
                    if messageinfo.messagestate == ACK_NOTACKED and (messageinfo.timestamp + ACKTIMEOUT) < now:
                        #resend NOTACKED message
                        logger("re-sending to %s, message %s" % (messageinfo.destination, messageinfo.message))
                        self.send(messageinfo.message, peer=messageinfo.destination, isresend=True)
                        messageinfo.timestamp = time.time()
                    elif DO_PERIODIC_PINGS and messageinfo.messagestate == ACK_ACKED and \
                            (messageinfo.timestamp + LIVENESSTIMEOUT) < now and \
                            messageinfo.destination in checkliveness:
                        checkliveness.remove(messageinfo.destination)
            except Exception as ec:
                logger("exception in resend: %s" % ec)
                
            if DO_PERIODIC_PINGS:
                for pingpeer in checkliveness:
                    logger("sending PING to %s" % pingpeer)
                    pingmessage = HandshakeMessage(MSG_PING, self.me)
                    self.send(pingmessage, peer=pingpeer)
            time.sleep(ACKTIMEOUT)

    def get_inputs(self):
        """Shellloop that accepts inputs from the command prompt and calls corresponding command
        handlers.
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
    
    # There are 3 basic send types: peer.send, conn.send and group.send
    # def __init__(self, message, destination, messagestate=ACK_NOTACKED, timestamp=0):
    def send(self, message, peer=None, group=None, isresend=False):
        if peer:
            connection = self.connectionpool.get_connection_by_peer(peer)
            if not isresend:
                msginfo = MessageInfo(message,peer,ACK_NOTACKED,time.time())
                with self.outstandingmessages_lock:
                    self.outstandingmessages[message.fullid()] = msginfo
            connection.send(message)
        elif group:
            assert not isresend, "performing a resend to a group"
            for peer in group.members:
                connection = self.connectionpool.get_connection_by_peer(peer)
                msginfo = MessageInfo(message,peer,ACK_NOTACKED,time.time())
                with self.outstandingmessages_lock:
                    self.outstandingmessages[message.fullid()] = msginfo
                connection.send(message)
                message = copy.copy(message)
                message.assignuniqueid()

    # asynchronous event handlers
    def terminate_handler(self, signal, frame):
        print self.me, "exiting.."
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)

    def interrupt_handler(self, signal, frame):
	print 'BYE!'
        sys.stdout.flush()
	sys.stderr.flush()
        os._exit(0)
