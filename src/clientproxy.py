'''
@author: denizalti
@note: The Client
@date: February 1, 2011
'''
import socket, os, sys, time, random
from threading import Thread, Lock, Condition
from enums import *
from utils import *
from connection import ConnectionPool, Connection
from group import Group
from peer import Peer
from message import ClientMessage, Message, PaxosMessage, HandshakeMessage, AckMessage
from command import Command
from pvalue import PValue, PValueSet
try:
    import dns
    import dns.resolver
except:
    print("Install dnspython: http://www.dnspython.org/")

REPLY = 0
CONDITION = 1

class ClientProxy():
    def __init__(self, bootstrap, debug=False):
        self.debug = debug
        self.domainname = None
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.socket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        self.bootstraplist = self.discoverbootstrap(bootstrap)
        if len(self.bootstraplist) == 0:
            if self.debug:
                print "No bootstrap found"
            self._graceexit()
        self.connecttobootstrap()
        myaddr = findOwnIP()
        myport = self.socket.getsockname()[1]
        self.me = Peer(myaddr,myport,NODE_CLIENT)
        self.logger = NetworkLogger("%s-%s" % ('NODE_CLIENT',self.me.getid()), 'egs-110.cs.cornell.edu:12000')
        self.commandnumber = random.randint(1, sys.maxint)
        self.lock = Lock()

    def _getipportpairs(self, bootaddr, bootport):
        for node in socket.getaddrinfo(bootaddr, bootport):
            yield Peer(node[4][0],bootport,NODE_REPLICA)

    def _getbootstrapfromdomain(self, domainname):
        try:
            answers = dns.resolver.query('_concoord._tcp.'+domainname, 'SRV')
            for rdata in answers:
                for peer in self._getipportpairs(str(rdata.target), rdata.port):
                    yield peer
        except dns.resolver.NXDOMAIN:
            pass

    def discoverbootstrap(self, givenbootstrap):
        tmpbootstraplist = []
        try:
            for bootstrap in givenbootstrap.split(","):
                # The bootstrap list is read only during initialization
                if bootstrap.find(":") >= 0:
                    bootaddr,bootport = bootstrap.split(":")
                    for peer in self._getipportpairs(bootaddr, int(bootport)):
                        tmpbootstraplist.append(peer)
                else:
                    self.domainname = bootstrap
                    for peer in self._getbootstrapfromdomain(self.domainname):
                        tmpbootstraplist.append(peer)
        except ValueError:
            if self.debug:
                print "bootstrap usage: ipaddr1:port1,ipaddr2:port2 or domainname"
            self._graceexit()
        return tmpbootstraplist

    def getbootstrapfromdomain(self, domainname):
        tmpbootstraplist = []
        for peer in self._getbootstrapfromdomain(self.domainname):
            tmpbootstraplist.append(peer)
        return tmpbootstraplist

    def connecttobootstrap(self):
        for bootpeer in self.bootstraplist:
            try:
                self.socket.close()
                self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                self.socket.connect((bootpeer.addr,bootpeer.port))
                self.conn = Connection(self.socket)
                self.bootstrap = bootpeer.addr,bootpeer.port #XXX
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

    def invoke_command(self, commandname, *args):
        with self.lock:
            mynumber = self.commandnumber
            self.commandnumber += 1
            argstr = " ".join(str(arg) for arg in args)
            commandstr = commandname + " " + argstr
            command = Command(self.me, mynumber, commandstr)
            cm = ClientMessage(MSG_CLIENTREQUEST, self.me, command)
            replied = False
            if self.debug:
                print "Initiating command %s" % str(command)
            starttime = time.time()
            try:
                self.conn.settimeout(CLIENTRESENDTIMEOUT)
            except:
                return "Cannot connect to object!"
            while not replied:
                try:
                    success = self.conn.send(cm)
                    if self.debug:
                        print "Bootstrap: ", self.bootstrap
                        print "Sent message %s" % str(cm)
                    if not success:
                        raise IOError
                    timestamp, reply = self.conn.receive()
                    if self.debug:
                        print "after receive  %s" % str(reply)
                    if reply and reply.type == MSG_CLIENTREPLY and reply.inresponseto == mynumber:
                        if reply.replycode == CR_REJECTED or reply.replycode == CR_LEADERNOTREADY:
                            raise IOError
                        elif reply.replycode == CR_INPROGRESS:
                            continue
                        else:
                            replied = True
                    if time.time() - starttime > CLIENTRESENDTIMEOUT:
                        if self.debug:
                            print "timed out: %d seconds" % CLIENTRESENDTIMEOUT
                        if reply and reply.type == MSG_CLIENTREPLY and reply.inresponseto == mynumber:
                            replied = True
                except ( IOError, EOFError ):
                    self._trynewbootstrap()
                except KeyboardInterrupt:
                    self._graceexit()
            if reply.replycode == CR_META:
                return
            elif reply.replycode == CR_EXCEPTION:
                raise Exception(reply.reply)
            elif reply.replycode == CR_BLOCK:
                # XXX
                return "Block."
            elif reply.replycode == CR_UNBLOCK:
                # XXX
                return "Unblock."    
            else:
                return reply.reply
            
    def _graceexit(self):
        return
  


    
