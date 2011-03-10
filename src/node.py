'''
@author: egs
@note: Master class for all nodes
@date: February 1, 2011
'''
from optparse import OptionParser
from threading import Thread, RLock, Lock, Condition, Timer
from time import sleep,time
import os
import time
import random
import socket
import select
import copy

from enums import *
from utils import *
from connection import ConnectionPool,Connection
from group import Group
from peer import Peer
from message import Message,PaxosMessage,HandshakeMessage,AckMessage,PValue,PValueSet,MessageInfo,Command

parser = OptionParser(usage="usage: %prog -p port -b bootstrap -d delay")
parser.add_option("-p", "--port", action="store", dest="port", type="int", default=6668, help="port for the node")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port:type triple for the bootstrap peer")
parser.add_option("-i", "--id", action="store", dest="accountid", type="int", default=0, help="[optional] id for the account")
(options, args) = parser.parse_args()

DO_PERIODIC_PINGS=False

class Node():
    """Node encloses the basic Node behaviour and state that
    are extended by Leaders, Acceptors or Replicas.
    """ 
    def __init__(self, mytype, port=options.port, bootstrap=options.bootstrap):
        """Initialize Node

        Node State
        - addr: hostname for Node, detected automatically
        - port: port for Node, can be taken from the commandline (-p [port]) or
        detected automatically by binding.
        - socket: socket of Node
        - connectionpool: ConnectionPool that keeps all Connections Node knows about
        - type: type of the corresponding Node: NODE_LEADER | NODE_ACCEPTOR | NODE_REPLICA
        - alive: liveness of Node
        - me: Peer object that represents Node
        - id: id for Node (addr:port)
        - groups: other Peers in the system that Node knows about. Node.groups is indexed by the
        corresponding node_name (NODE_LEADER | NODE_ACCEPTOR | NODE_REPLICA), which returns a Group
        """
        self.addr = findOwnIP()
        self.port = port
        self.connectionpool = ConnectionPool()
        self.type = mytype
        self.alive = True
        self.outstandingmessages_lock = RLock()
        self.outstandingmessages = {} # keeps <messageid:messageinfo> mappings as <MessageID:MessageInfo> objects
        self.lock = Lock()

        # create server socket and bind to a port
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        for i in range(30):
            try:
                self.socket.bind((self.addr,self.port))
                break
            except:
                self.port += 1
        self.socket.listen(10)

        # initialize empty groups
        self.me = Peer(self.addr,self.port,self.type)
        self.id = self.me.id()
        setlogprefix(self.id)
        logger("I'm alive.")
        self.groups = {NODE_ACCEPTOR:Group(self.me), NODE_REPLICA: Group(self.me), NODE_LEADER:Group(self.me)}

        # connect to the bootstrap node
        if bootstrap:
            logger("connecting to %s" % bootstrap)
            bootaddr,bootport = bootstrap.split(":")
            bootpeer = Peer(bootaddr,int(bootport))
            helomessage = HandshakeMessage(MSG_HELO, self.me)
            self.send(helomessage, peer=bootpeer)

    def startservice(self):
        """Start a server, a shell and a ping thread"""
        # Start a thread with the server which will start a thread for each request
        server_thread = Thread(target=self.server_loop)
        server_thread.start()
        # Start a thread that waits for inputs
        input_thread = Thread(target=self.get_inputs)
        input_thread.start()
        # Start a thread that pings neighbors
        timer_thread = Timer(ACKTIMEOUT/5, self.periodic)
        timer_thread.start()
        
    def __str__(self):
        """Return Node information (addr:port)"""
        return "%s  %s:%d" % (node_names[self.type], self.addr, self.port)

    def statestr(self):
        """Return the Peers Node knows of, i.e. connectivity state"""
        returnstr = "state:\n"
        for type,group in self.groups.iteritems():
            returnstr += str(group)
        returnstr += "\nPending:\n"
        for cno,proposal in self.pendingcommands.iteritems():
            returnstr += "command#%d: %s" % (cno, proposal)
        return returnstr

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
        nascentset = []
        while self.alive:
            try:
                # collect the set of all sockets that we want to listen to
                socketset = [self.socket]  # add the server socket
                for conn in self.connectionpool.poolbypeer.itervalues():
                    sock = conn.thesocket
                    if sock is not None:
                        socketset.append(sock)
                try:
                    for conn in self.clientpool.poolbypeer.itervalues():
                        sock = conn.thesocket
                        if sock is not None:
                            socketset.append(sock)
                except AttributeError:
                    pass
                for s,timestamp in nascentset:
                    # prune and close old sockets that never got turned into connections
                    if time.time() - timestamp > HELOTIMEOUT:
                        # expired -- if it's not already in the set, it should be closed
                        if s not in socketset:
                            logger("Removing %s from the nascentset" % s)
                            nascentset.remove((s,timestamp))
                            s.close()
                    elif s not in socketset:
                        # check if it has been added before
                        socketset.append(s)
                        
                assert len(socketset) == len(set(socketset)), "[%s] socketset has Duplicates." % self
                inputready,outputready,exceptready = select.select(socketset,[],socketset)
                
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
                                logger("Removing %s from the nascentset" % s)
                                nascentset.remove((s,timestamp))
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
        if message.type == MSG_ACK:
            with self.outstandingmessages_lock:
                ackid = "%s+%d" % (self.me.id(), message.ackid)
                logger("got ack message %s" % ackid)
                if self.outstandingmessages.has_key(ackid):
                    logger("deleting outstanding message %s" % ackid)
                    del self.outstandingmessages[ackid]
                else:
                    logger("acked message %s not in outstanding messages" % ackid)
        else:
            logger("got message (about to ack) %s" % message.fullid())
            if message.type != MSG_CLIENTREQUEST:
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
        """Add the other peer into the connection pool and group"""
        self.groups[msg.source.type].add(msg.source)
        self.connectionpool.add_connection_to_peer(msg.source,conn)
        heloreplymessage = HandshakeMessage(MSG_HELOREPLY, self.me, self.groups)
        self.send(heloreplymessage, peer=msg.source)

    def msg_bye(self, conn, msg):
        """Handler for MSG_BYE
        Deletes the source of MSG_BYE from groups
        """
        self.groups[msg.source.type].remove(msg.source)
    #
    # shell commands generic to all nodes
    #
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
        self.send(byemessage, peer=self)
                    
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
                    for id, messageinfo in self.outstandingmessages.iteritems():
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
                logger("Exception in Resend: %s" % ec)
                
            if DO_PERIODIC_PINGS:
                for pingpeer in checkliveness:
                    logger("Sending PING to %s" % pingpeer)
                    helomessage = HandshakeMessage(MSG_HELO, self.me)
                    self.send(helomessage, peer=pingpeer)

            if self.type == NODE_REPLICA or self.type == NODE_LEADER:
                currentleader = self.find_leader()
                #print "XXXX: ", currentleader
                if currentleader != None and currentleader != self.me:
                    logger("Sending PING to %s" % currentleader)
                    helomessage = HandshakeMessage(MSG_HELO, self.me)
                    self.send(helomessage, peer=pingpeer)

            time.sleep(ACKTIMEOUT/5)

    def get_inputs(self):
        """Shellloop that accepts inputs from the command prompt and calls corresponding command
        handlers.
        """
        while self.alive:
            try:
                input = raw_input("paxos-shell> ")
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
            logger("Sending message %s to %s" % (message.fullid(), peer))
            if not isresend:
                msginfo = MessageInfo(message,peer,ACK_NOTACKED,time.time())
                with self.outstandingmessages_lock:
                    self.outstandingmessages[message.fullid()] = msginfo
            connection.send(message)
        elif group:
            assert not isresend, "performing a resend to a group"
            for peer in group.members:
                logger("Sending message to %s" % peer)
                connection = self.connectionpool.get_connection_by_peer(peer)
                with self.outstandingmessages_lock:
                    msginfo = MessageInfo(message,peer,ACK_NOTACKED,time.time())
                    self.outstandingmessages[message.fullid()] = msginfo
                connection.send(message)
                message = copy.copy(message)
                message.assignuniqueid()
         
