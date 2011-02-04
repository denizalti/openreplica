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

from enums import *
from utils import *
from communicationutils import *
from connection import *
from group import *
from peer import *
from message import *
from scout import *
from commander import *
from bank import *

parser = OptionParser(usage="usage: %prog -p port -b bootstrap -d delay")
parser.add_option("-p", "--port", action="store", dest="port", type="int", default=6668, help="port for the node")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port:type triple for the bootstrap peer")
(options, args) = parser.parse_args()

# TIMEOUT THREAD
class Node():
    def __init__(self, mytype, port=options.port, bootstrap=options.bootstrap):
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
        self.clients = Group(self.me)

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
        # Start a thread with the server which will start a thread for each request
        server_thread = Thread(target=self.serverLoop)
        server_thread.start()
        # Start a thread that waits for inputs
        input_thread = Thread(target=self.getInputs)
        input_thread.start()
        
    def __str__(self):
        return "%s:%d" % (self.addr, self.port)

    def statestr(self):
        returnstr = "state: "
        for type,group in self.groups.iteritems():
            returnstr += str(group)
        return returnstr
    
    def serverLoop(self):
        while self.alive:
            try:
                clientsock,clientaddr = self.socket.accept()
                print "[%s] accepted a connection from address %s" % (self,clientaddr)
                # Start a Thread
                Thread(target=self.handleConnection,args =[clientsock]).start()
            except KeyboardInterrupt, EOFError:
                os._exit(0)
        self.socket.close()
        return
        
    def msg_helo(self, conn, msg):
        print "[%s] got a helo message" % self
        replymsg = HandshakeMessage(MSG_HELOREPLY,self.me,self.groups)
        # XXX THIS IS WRONG!!!!
        # XXX we need consensus on who to add to which group
        # add the other peer to the right peer group
        self.groups[msg.source.type].add(msg.source)
        conn.send(replymsg)

    def msg_heloreply(self, conn, msg):
        for type,group in self.groups.iteritems():
            group.mergeList(msg.groups[type])

    def msg_bye(self, conn, msg):
        self.groups[msg.source.type].remove(msg.source)

    def handleConnection(self, clientsock):
#        print "[%s] server loop ..." % self
        connection = Connection(clientsock)
        while True:
            message = connection.receive()
            print "[%s] got message %s" % (self.id, message)
            
            mname = "msg_%s" % msg_names[message.type].lower()
            try:
                method = getattr(self, mname)
            except AttributeError:
                print "message not supported: %s" % (message)
            method(connection, message)
        clientsock.close()

    # shell commands generic to all nodes
    def cmd_help(self, args):
        print "Commands I support:"
        for attr in dir(self):
            if attr.startswith("cmd_"):
                print attr.replace("cmd_", "")

    def cmd_exit(self, args):
        self.alive = False
        byeMessage = Message(MSG_BYE,source=self.me)
        for type,group in self.groups.iteritems():
            group.broadcast(byeMessage)
        self.me.send(byeMessage)
                    
    def cmd_state(self, args):
        print "[%s] %s\n" % (self, self.statestr())

    def getInputs(self):
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
                    method(input)
            except (KeyboardInterrupt, EOFError):
                os._exit(0)
        return
                    
