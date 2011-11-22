'''
@author: denizalti
@note: The Client
@date: February 1, 2011
'''
import socket, os, sys, time
from threading import Thread, Lock, Condition
from enums import *
from utils import *
from connection import ConnectionPool, Connection
from group import Group
from peer import Peer
from message import ClientMessage, Message, PaxosMessage, HandshakeMessage, AckMessage
from command import Command
from pvalue import PValue, PValueSet

REPLY = 0
CONDITION = 1

class ClientProxy():
    def __init__(self, bootstrap, debug=False):
        self.debug = debug
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.socket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        self.bootstraplist = []
        self.discoverbootstrap(bootstrap)
        self.connecttobootstrap()
        myaddr = findOwnIP()
        myport = self.socket.getsockname()[1]
        self.me = Peer(myaddr,myport,NODE_CLIENT) 
        self.alive = True
        self.clientcommandnumber = 1
        self.commandlistcond = Condition()
        self.commandlist = []
        self.requests = {} # Keeps request:(reply, condition) mappings
        setlogprefix("%s %s" % ('NODE_CLIENT',self.me.getid()))
        self.startclientproxy()

    def _getipportpairs(self, bootaddr, bootport):
        for node in socket.getaddrinfo(bootaddr, bootport):
            yield Peer(node[4][0],bootport,NODE_REPLICA)

    def _getbootstrapfromdomain(self, domainname):
        answers = dns.resolver.query('_concoord._tcp.hack.'+domainname, 'SRV')
        for rdata in answers:
            for peer in self._getipportpairs(str(rdata.target), rdata.port):
                yield peer
            
    def discoverbootstrap(self, givenbootstrap):
        bootstrapstrlist = givenbootstrap.split(",")
        try:
            for bootstrap in bootstrapstrlist:
                # The bootstrap list is read only during initialization
                if bootstrap.find(":") >= 0:
                    bootaddr,bootport = bootstrap.split(":")
                    for peer in self._getipportpairs(bootaddr, int(bootport)):
                        self.bootstraplist.append(peer)
                else:
                    self.domainname = bootstrap
                    for peer in self._getbootstrapfromdomain(self.domainname):
                        self.bootstraplist.append(peer)
        except ValueError:
            print "bootstrap usage: ipaddr1:port1,ipaddr2:port2 or domainname"
            self._graceexit()

    def getbootstrapfromdomain(self, domainname):
        tmpbootstraplist = []
        for peer in self._getbootstrapfromdomain(self.domainname):
            tmpbootstraplist.append(peer)
        self.bootstraplist = tmpbootstraplist

    def connecttobootstrap(self):
        for bootpeer in self.bootstraplist:
            try:
                self.socket.close()
                self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                self.socket.connect((bootpeer.addr,bootpeer.port))
                self.conn = Connection(self.socket)
                if self.debug:
                    print "Connected to new bootstrap: ", bootpeer.addr,bootpeer.port
                break
            except socket.error, e:
                if self.debug:
                    print e
                continue

    def _trynewbootstrap(self):
        if self.domainname:
            self.getbootstrapfromdomain(self.domainname)
        else:
            oldbootstrap = self.bootstraplist.pop(0)
            self.bootstraplist.append(oldbootstrap)
        self.connecttobootstrap()

    def startclientproxy(self):
        clientloop_thread = Thread(target=self.clientloop)
        clientloop_thread.start()

    def invoke_command(self, commandname, *args):
        print "Invoking command"
        mynumber = self.clientcommandnumber
        self.clientcommandnumber += 1
        argstr = " ".join(str(arg) for arg in args)
        commandstr = commandname + " " + argstr
        print commandstr
        newcommand = Command(self.me, mynumber, commandstr)
        with self.commandlistcond:
            self.commandlist.append(newcommand)
            self.requests[newcommand] = (None,Condition())
            self.commandlistcond.notify()
        # Wait for the reply
        with self.requests[newcommand][CONDITION]:
            while self.requests[newcommand][REPLY] == None:
                self.requests[newcommand][CONDITION].wait()
            # Check if there are exceptions and raise them.
            if self.requests[newcommand][REPLY].type == MSG_CLIENTMETAREPLY:
                print "Client METAREPLY"
                if self.requests[newcommand][REPLY].replycode == CR_META:
                    print "This is not used."
                elif self.requests[newcommand][REPLY].replycode == CR_EXCEPTION:
                    raise self.requests[newcommand][REPLY].reply
                elif self.requests[newcommand][REPLY].replycode == CR_BLOCK:
                    print "Blocking client."
                elif self.requests[newcommand][REPLY].replycode == CR_UNBLOCK:
                    print "Unblocking client."    
            else:
                return self.requests[newcommand][REPLY].reply
    
    def clientloop(self):
        while self.alive:
            try:
                with self.commandlistcond:
                    while len(self.commandlist) == 0:
                        self.commandlistcond.wait()
                    command = self.commandlist.pop(0)
                mycommand = command
                cm = ClientMessage(MSG_CLIENTREQUEST, self.me, command)
                replied = False
                if self.debug:
                    print "Initiating command %s" % str(command)
                starttime = time.time()
                self.conn.settimeout(CLIENTRESENDTIMEOUT)

                while not replied:
                    success = self.conn.send(cm)
                    if not success:
                        self._trynewbootstrap()
                        continue
                    try:
                        timestamp, reply = self.conn.receive()
                    except KeyboardInterrupt:
                        self._graceexit()
                    if reply and reply.type == MSG_CLIENTREPLY and reply.inresponseto == mycommand.clientcommandnumber:
                        if reply.replycode == CR_REJECTED or reply.replycode == CR_LEADERNOTREADY:
                            self._trynewbootstrap()
                            continue
                        elif reply.replycode == CR_INPROGRESS:
                            continue
                        else:
                            replied = True
                            with self.requests[mycommand][CONDITION]:
                                self.requests[mycommand] = (reply,self.requests[mycommand][CONDITION])
                                self.requests[mycommand][CONDITION].notify()
                    elif reply and reply.type == MSG_CLIENTMETAREPLY and reply.inresponseto == mycommand.clientcommandnumber:
                        # XXX Block/Unblock the client if necessary
                        print "Handling METAREPLY.."
                    if time.time() - starttime > CLIENTRESENDTIMEOUT:
                        if self.debug:
                            print "timed out: %d seconds" % CLIENTRESENDTIMEOUT
                        if reply and reply.type == MSG_CLIENTREPLY and reply.inresponseto == mycommand.clientcommandnumber:
                            replied = True
                            with self.requests[mycommand][CONDITION]:
                                self.requests[mycommand] = (reply,self.requests[mycommand][CONDITION])
                                self.requests[mycommand][CONDITION].notify()
            except ( IOError, EOFError ):
                self._graceexit()
            except KeyboardInterrupt:
                self._graceexit()

    def terminate_handler(self, signal, frame):
        self._graceexit()
        
    def _graceexit(self):
        return
  


    
