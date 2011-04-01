'''
@author: denizalti
@note: The Client
@date: February 1, 2011
'''
import socket
from optparse import OptionParser
from threading import Thread, Lock, Condition

from node import Node
from enums import *
from utils import findOwnIP
from connection import ConnectionPool, Connection
from group import Group
from peer import Peer
from message import ClientMessage,Message,PaxosMessage,HandshakeMessage,AckMessage,PValue,PValueSet, Command
import os
import time

parser = OptionParser(usage="usage: %prog -b bootstrap")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port tuples separated with commas for bootstrap peers")
(options, args) = parser.parse_args()

class Client():
    """Client sends requests and receives responses"""
    def __init__(self, givenbootstraplist):
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
    
    def clientloop(self):
        """Accepts commands from the prompt and sends requests for the commands
        and receives corresponding replies."""
        while self.alive:
            inputcount = 0
            try:
                shellinput = raw_input("client-shell> ")
                if len(shellinput) == 0:
                    continue
                else:
                    inputcount += 1
                    mynumber = self.clientcommandnumber
                    self.clientcommandnumber += 1
                    
                    command = Command(self.me, mynumber, shellinput)
                    cm = ClientMessage(MSG_CLIENTREQUEST, self.me, command)
                    replied = False
                    print "Client Message about to be sent:", cm
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
                        if time.time() - starttime > CLIENTRESENDTIMEOUT:
                            if reply and reply.type == MSG_CLIENTREPLY and reply.inresponseto == mynumber:
                                replied = True
            except ( IOError, EOFError ):
                os._exit(0)
        
theClient = Client(options.bootstrap)
theClient.clientloop()

  


    
