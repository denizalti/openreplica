'''
@author: egs
@note: Master class for all nodes
@date: February 1, 2011
'''
from optparse import OptionParser
from threading import Thread, Lock, Condition
import os
import time
import random
import socket
import select

from enums import *
from utils import findOwnIP
from connection import ConnectionPool,Connection
from group import Group
from peer import Peer
from message import Message,PaxosMessage,HandshakeMessage,PValue,PValueSet

parser = OptionParser(usage="usage: %prog -p port -b bootstrap -d delay")
parser.add_option("-p", "--port", action="store", dest="port", type="int", default=6668, help="port for the node")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port:type triple for the bootstrap peer")
parser.add_option("-i", "--id", action="store", dest="accountid", type="int", default=0, help="[optional] id for the account")
(options, args) = parser.parse_args()

# TIMEOUT THREAD
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
        self.groups = {NODE_ACCEPTOR:Group(self.me), NODE_REPLICA: Group(self.me), NODE_LEADER:Group(self.me)}

        # connect to the bootstrap node
        print "[%s] starting up..." % self
        if bootstrap:
            print "[%s] connecting to %s" % (self,bootstrap)
            bootaddr,bootport = bootstrap.split(":")
            bootpeer = Peer(bootaddr,int(bootport))
            helomessage = HandshakeMessage(MSG_HELO, self.me)
            heloreply = bootpeer.sendWaitReply(self, helomessage)
            print "[%s] received %s" % (self, heloreply)
            bootpeer = heloreply.source
            self.groups[bootpeer.type].add(bootpeer)
            
            for type,group in self.groups.iteritems():
                group.union(heloreply.groups[type])

    def startservice(self):
        """Start a server and a shell thread"""
        # Start a thread with the server which will start a thread for each request
        server_thread = Thread(target=self.serverLoop)
        server_thread.start()
        # Start a thread that waits for inputs
        input_thread = Thread(target=self.getInputs)
        input_thread.start()
        
    def __str__(self):
        """Return Node information (addr:port)"""
        return "%s  %s:%d" % (node_names[self.type], self.addr, self.port)

    def statestr(self):
        """Return the Peers Node knows of, i.e. connectivity state"""
        returnstr = "state: "
        for type,group in self.groups.iteritems():
            returnstr += str(group)
        return returnstr
    
    def serverLoop(self):
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
                    socketset.append(conn.thesocket)
                for s,timestamp in nascentset:
                    # prune and close old sockets that never got turned into connections
                    if time.time() - timestamp > HELOTIMEOUT:
                        # expired -- if it's not already in the set, it should be closed
                        if s not in socketset:
                            nascentset.remove((s,timestamp))
                            s.close()
                    elif s not in socketset:
                        # check if it has been added before
                        socketset.append(s)
                        
                assert len(socketset) == len(set(socketset)), "[%s] socketset has Duplicates." % self
                inputready,outputready,exceptready = select.select(socketset,[],socketset)
                
                for s in inputready:
                    if s == self.socket:
                        clientsock,clientaddr = self.socket.accept()
                        print "[%s] accepted a connection from address %s" % (self,clientaddr)
                        nascentset.append((clientsock,time.time()))
                    else:
                        self.handleConnection(s)
            except KeyboardInterrupt, EOFError:
                os._exit(0)
        self.socket.close()
        return
        
    def handleConnection(self, clientsock):
        """Receives a message and calls the corresponding message handler"""
        connection = self.connectionpool.getConnectionBySocket(clientsock)
        message = connection.receive()
        print "[%s] got message %s" % (self.id, message)
        mname = "msg_%s" % msg_names[message.type].lower()
        try:
            method = getattr(self, mname)
        except AttributeError:
            print "message not supported: %s" % (message)
            return
        method(connection, message)

    #
    # message handlers
    #
    def msg_helo(self, conn, msg):
        """Handler for MSG_HELO"""
        print "[%s] got a helo message" % self
        replymsg = HandshakeMessage(MSG_HELOREPLY,self.me,self.groups)
        # XXX THIS IS WRONG!!!!
        # XXX we need consensus on who to add to which group
        # add the other peer to the right peer group
        if msg.source.type == NODE_CLIENT:
            self.clients.add(msg.source)
        else:
            self.groups[msg.source.type].add(msg.source)
        self.connectionpool.addConnectionToPeer(msg.source, conn)
        conn.send(replymsg)

    def msg_heloreply(self, conn, msg):
        """Handler for MSG_HELOREPLY
        Merges own Peer Groups with the ones in the MSG_HELOREPLY
        """
        for type,group in self.groups.iteritems():
            group.mergeList(msg.groups[type])

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
        byeMessage = Message(MSG_BYE,self.me)
        for type,group in self.groups.iteritems():
            group.broadcast(self, byeMessage)
        self.me.send(self, byeMessage)
                    
    def cmd_state(self, args):
        """Shell command [state]: Prints connectivity state of the corresponding Node."""
        print "[%s] %s\n" % (self, self.statestr())

    def getInputs(self):
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
                    method(input)
            except ( KeyboardInterrupt,EOFError ):
                os._exit(0)
        return
                    
