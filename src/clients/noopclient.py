'''
@author: denizalti
@note: The noop Client
@date: August 8, 2011
'''
import socket
from optparse import OptionParser
from enums import *
from utils import findOwnIP
from connection import ConnectionPool, Connection
from group import Group
from peer import Peer
from message import ClientMessage, Message, PaxosMessage, HandshakeMessage, AckMessage
from command import Command
from pvalue import PValue, PValueSet
import os
import sys
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
                continue
    
    def clientloop(self):
        """Creates and send noop"""
        while self.alive:
            mynumber = self.clientcommandnumber
            self.clientcommandnumber += 1
            # create command from input
            command = Command(self.me, mynumber, "noop")
            cm = ClientMessage(MSG_CLIENTREQUEST, self.me, command)
            replied = False
            print "Client Message about to be sent:", cm
            starttime = time.time()
            self.conn.settimeout(CLIENTRESENDTIMEOUT)
            success = self.conn.send(cm)
            # problem with the connection, try another bootstrap
            if not success:
                currentbootstrap = self.bootstraplist.pop(0)
                self.bootstraplist.append(currentbootstrap)
                self.connecttobootstrap()
                continue
            reply = self.conn.receive()
            if reply and (reply.type == MSG_CLIENTREPLY or reply.type == MSG_CLIENTMETAREPLY) and reply.inresponseto == mynumber:
                if reply.replycode == CR_REJECTED or reply.replycode == CR_LEADERNOTREADY:
                    currentbootstrap = self.bootstraplist.pop(0)
                    self.bootstraplist.append(currentbootstrap)
                    self.connecttobootstrap()
                    continue
                elif reply.replycode == CR_INPROGRESS:
                    continue
                else:
                    replied = True   
            if time.time() - starttime > CLIENTRESENDTIMEOUT:
                if reply and reply.type == MSG_CLIENTREPLY and reply.inresponseto == mynumber:
                        replied = True
            sys.stdout.flush()
        
theClient = Client(options.bootstrap)
theClient.clientloop()
  


    
