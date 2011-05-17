'''
@author: denizalti
@note: The Client
@date: February 1, 2011
'''
import socket
from optparse import OptionParser
from threading import Thread, Lock, Condition
from enums import *
from utils import findOwnIP
from connection import ConnectionPool, Connection
from group import Group
from peer import Peer
from message import ClientMessage, Message, PaxosMessage, HandshakeMessage, AckMessage
from command import Command
from pvalue import PValue, PValueSet
import os
import time

parser = OptionParser(usage="usage: %prog -b bootstrap")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port tuples separated with commas for bootstrap peers")
parser.add_option("-f", "--file", action="store", dest="filename", default=None, help="inputfile")
(options, args) = parser.parse_args()

class Client():
    """Client sends requests and receives responses"""
    def __init__(self, givenbootstraplist, inputfile):
        """Initialize Client

        Client State
        - socket: socket of Client
        - me: Peer instance of Client
        - conn: Connection on Client's socket
        - alive: liveness of Client
        """
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.initializebootstraplist(givenbootstraplist)
        self.connecttobootstrap()
        myaddr = findOwnIP()
        myport = self.socket.getsockname()[1] 
        self.me = Peer(myaddr,myport,NODE_CLIENT)
        self.alive = True
        self.clientcommandnumber = 1
        self.commandlistcond = Condition()
        self.commandlist = []

    def startclientproxy():
        clientloop_thread = Thread(target=self.clientloop)
        clientloop_thread.start()

    def initializebootstraplist(self,givenbootstraplist):
        bootstrapstrlist = givenbootstraplist.split(",")
        self.bootstraplist = []
        for bootstrap in bootstrapstrlist:
            bootaddr,bootport = bootstrap.split(":")
            bootpeer = Peer(bootaddr,int(bootport),NODE_REPLICA)
            self.bootstraplist.append(bootpeer)

    def connecttobootstrap(self):
        for bootpeer in self.bootstraplist:
            try:
                print "Connecting to new bootstrap: ", bootpeer.addr,bootpeer.port
                self.socket.close()
                self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                self.socket.connect((bootpeer.addr,bootpeer.port))
                self.conn = Connection(self.socket)
                print "Connected to new bootstrap: ", bootpeer.addr,bootpeer.port
                break
            except socket.error, e:
                print e
                continue

    def invoke_command(self, args):
        mynumber = self.clientcommandnumber
        self.clientcommandnumber += 1
        newcommand = Command(self.me, mynumber, args)
        with self.commandlistcond:
            self.commandlist.append(newcommand)
            self.commandlistcond.notify()
    
    def clientloop(self):
        """Accepts commands from the prompt and sends requests for the commands
        and receives corresponding replies."""
        while self.alive:
            with self.commandlistcond:
                while len(self.commandlist) == 0:
                    self.commandlistcond.wait()
                command = self.commandlist.pop(0)
            cm = ClientMessage(MSG_CLIENTREQUEST, self.me, command)
            replied = False
            #print "Client Message about to be sent:", cm
            starttime = time.time()
            self.conn.settimeout(CLIENTRESENDTIMEOUT)
            
            while not replied:
                success = self.conn.send(cm)
                if not success:
                    currentbootstrap = self.bootstraplist.pop(0)
                    self.bootstraplist.append(currentbootstrap)
                    self.connecttobootstrap()
                    continue
                reply = self.conn.receive()
                print "received: ", reply
                if reply and reply.type == MSG_CLIENTREPLY and reply.inresponseto == mynumber:
                    if reply.command == "REJECTED" or reply.command == "LEADERNOTREADY":
                        currentbootstrap = self.bootstraplist.pop(0)
                        self.bootstraplist.append(currentbootstrap)
                        self.connecttobootstrap()
                        continue
                    else:
                        replied = True
                elif reply and reply.type == MSG_CLIENTMETAREPLY and reply.inresponseto == mynumber:
                    pass
                if time.time() - starttime > CLIENTRESENDTIMEOUT:
                    if reply and reply.type == MSG_CLIENTREPLY and reply.inresponseto == mynumber:
                        replied = True

theClient = Client(options.bootstrap, options.filename)
theClient.clientloop()

  


    
