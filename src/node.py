'''
@author: egs
@note: Master class for all nodes
@date: February 1, 2011
'''
from optparse import OptionParser
from threading import Thread, Lock, Condition
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
    def __init__(self, port=options.port, bootstrap=options.bootstrap):
        self.addr = findOwnIP()
        self.port = port
        self.id = "%s:%d" % (self.addr,self.port)
        self.type = NODE_LEADER
        self.toPeer = Peer(self.id,self.addr,self.port,self.type)
        # groups
        self.groups = {NODE_ACCEPTOR:Group(self.toPeer), \
                       NODE_REPLICA: Group(self.toPeer), \
                       NODE_LEADER:Group(self.toPeer)}
        self.clients = Group(self.toPeer)
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
        print "bound to port %d" % self.port
        self.socket.listen(10)

        print "Node: %s" % self.id
        if bootstrap:
            print "connecting to %s" % bootstrap
            bootaddr,bootport = bootstrap.split(":")
            bootid = createID(bootaddr,bootport)
            bootpeer = Peer(bootid,bootaddr,int(bootport))
            helomessage = Message(type=MSG_HELO,source=self.toPeer.serialize())
            heloreply = Message(bootpeer.sendWaitReply(helomessage))
            bootpeer = Peer(heloreply.source[0],heloreply.source[1],heloreply.source[2],heloreply.source[3])
            self.groups[bootpeer.type].add(bootpeer)
            for type,group in self.groups.iteritems():
                group.mergeList(heloreply.groups[type])

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
                print "DEBUG: Accepted a connection on socket:",clientsock," and address:",clientaddr
                # Start a Thread
                Thread(target=self.handleConnection,args =[clientsock]).start()
            except KeyboardInterrupt:
                break
        self.socket.close()
        return
        
    def cmd_help(self, args):
        print "Commands I support:"
        for attr in self.__dict__:
            if attr.startswith("cmd_"):
                print attr

    def cmd_exit(self, args):
        self.alive = False
        byeMessage = Message(type=MSG_BYE,source=self.toPeer.serialize())
        for type,group in self.groups.iteritems():
            group.broadcast(byeMessage)
        self.toPeer.send(byeMessage)
                    
    def cmd_state(self, args):
        print "[%s] %s\n" % (self, self.statestr())

    def getInputs(self):
        while self.alive:
            input = raw_input("What should I do? ")
            if len(input) == 0:
                print "I'm listening.."
            else:
                input = input.split()
                mname = "cmd_%s" % input[0].lower()
                try:
                    method = getattr(self, mname)
                    method(input)
                except AttributeError:
                    print "command not supported"
        return
                    
