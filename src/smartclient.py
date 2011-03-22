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
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port:type triple for the bootstrap peer")
(options, args) = parser.parse_args()

class Client():
    """Client sends requests and receives responses"""
    def __init__(self, bootstrap):
        """Initialize Client

        Client State
        - socket: socket of Client
        - me: Peer instance of Client
        - conn: Connection on Client's socket
        - alive: liveness of Client
        """
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        bootaddr,bootport = bootstrap.split(":")
        self.socket.connect((bootaddr,int(bootport)))
        myaddr = findOwnIP()
        myport = self.socket.getsockname()[1]
        self.me = Peer(myaddr,myport,NODE_CLIENT)
        self.conn = Connection(self.socket)
        self.alive = True
        self.clientcommandnumber = 1
        
    def clientloop(self):
        """Accepts commands from the prompt and sends requests for the commands
        and receives corresponding replies.
        """
        while self.alive:
            try:
                socketset = [self.socket]  # add the socket
                        
                assert len(socketset) == len(set(socketset)), "[%s] socketset has Duplicates." % self
                inputready,outputready,exceptready = select.select(socketset,[],socketset)
                
                for s in exceptready:
                    print "EXCEPTION ", s
                for s in inputready:
                    if s == self.socket:
                        clientsock,clientaddr = self.socket.accept()
                        logger("accepted a connection from address %s" % str(clientaddr))
                        success = True
                    else:
                        success = self.handle_connection(s)
                    if not success:
                        # s is closed, take it out of nascentset and connection pool
                        for sock,timestamp in nascentset:
                            if sock == s:
                                logger("removing %s from the nascentset" % s)
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
                if self.outstandingmessages.has_key(ackid):
                    #logger("deleting outstanding message %s" % ackid)
                    del self.outstandingmessages[ackid]
                else:
                    logger("acked message %s not in outstanding messages" % ackid)
        else:
            #logger("got message (about to ack) %s" % message.fullid())
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
                        print inputcount, "REPLIED: " if replied else "NOTREPLIED"
                        self.conn.send(cm)
                        reply = self.conn.receive()
                        print "received: ", reply
                        if time.time() - starttime > CLIENTRESENDTIMEOUT:
                            print "bootstrap node failed to respond in time"
                        if reply and reply.type == MSG_CLIENTREPLY and reply.inresponseto == mynumber:
                            replied = True
            except ( KeyboardInterrupt,EOFError ):
                os._exit(0)
        return
        
theClient = Client(options.bootstrap)
theClient.clientloop()

  


    
