'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: ConCoord Client Proxy
@copyright: See LICENSE
'''
import socket, os, sys, time, random, threading
from threading import Thread, Lock
import pickle
from concoord.enums import *
from concoord.utils import *
from concoord.exception import *
from concoord.connection import ConnectionPool, Connection
from concoord.group import Group
from concoord.peer import Peer
from concoord.message import ClientMessage, Message, PaxosMessage, HandshakeMessage, AckMessage
from concoord.command import Command
from concoord.pvalue import PValue, PValueSet
try:
    import dns
    import dns.resolver
    import dns.exception
except:
    print("Install dnspython: http://www.dnspython.org/")

REPLY = 0
CONDITION = 1

class ClientProxy():
    def __init__(self, bootstrap, timeout=60, debug=True):
        self.debug = debug
        self.timeout = timeout 
        self.domainname = None
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.socket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        self.bootstraplist = self.discoverbootstrap(bootstrap)
        if len(self.bootstraplist) == 0:
            raise ConnectionError("No bootstrap found")
        if not self.connecttobootstrap():
            raise ConnectionError("Cannot connect to any bootstrap")
        myaddr = findOwnIP()
        myport = self.socket.getsockname()[1]
        self.me = Peer(myaddr,myport,NODE_CLIENT)
        self.commandnumber = random.randint(1, sys.maxint)

        # synchronization
        self.lock = Lock()

    def getipportpairs(self, bootaddr, bootport):
        for node in socket.getaddrinfo(bootaddr, bootport):
            yield (node[4][0],bootport)

    def getbootstrapfromdomain(self, domainname):
        tmpbootstraplist = []
        try:
            answers = dns.resolver.query('_concoord._tcp.'+domainname, 'SRV')
            for rdata in answers:
                for peer in self.getipportpairs(str(rdata.target), rdata.port):
                    if peer not in tmpbootstraplist:
                        tmpbootstraplist.append(peer)
        except (dns.resolver.NXDOMAIN, dns.exception.Timeout):
            if self.debug:
                print "Cannot resolve name"
        return tmpbootstraplist

    def discoverbootstrap(self, givenbootstrap):
        tmpbootstraplist = []
        try:
            for bootstrap in givenbootstrap.split(","):
                # The bootstrap list is read only during initialization
                if bootstrap.find(":") >= 0:
                    bootaddr,bootport = bootstrap.split(":")
                    for peer in self.getipportpairs(bootaddr, int(bootport)):
                        if peer not in tmpbootstraplist:
                            tmpbootstraplist.append(peer)
                else:
                    self.domainname = bootstrap
                    tmpbootstraplist = self.getbootstrapfromdomain(self.domainname)
        except ValueError:
            if self.debug:
                print "bootstrap usage: ipaddr1:port1,ipaddr2:port2 or domainname"
            self._graceexit()
        return tmpbootstraplist

    def connecttobootstrap(self):
        connected = False
        for boottuple in self.bootstraplist:
            try:
                self.socket.close()
                self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                self.socket.connect(boottuple)
                self.conn = Connection(self.socket)
                self.conn.settimeout(CLIENTRESENDTIMEOUT)
                self.bootstrap = boottuple
                connected = True
                if self.debug:
                    print "Connected to new bootstrap: ", boottuple
                break
            except socket.error, e:
                if self.debug:
                    print e
                continue
        return connected

    def trynewbootstrap(self, triedreplicas):
        if self.domainname:
            self.bootstraplist = self.getbootstrapfromdomain(self.domainname)
        else:
            oldbootstrap = self.bootstraplist.pop(0)
            self.bootstraplist.append(oldbootstrap)
        if triedreplicas == set(self.bootstraplist):
            # If all replicas in the list are tried already, return False
            return False
        return self.connecttobootstrap()

    def invoke_command(self, *args):
        with self.lock:
            mynumber = self.commandnumber
            self.commandnumber += 1
            command = Command(self.me, mynumber, args)
            cm = ClientMessage(MSG_CLIENTREQUEST, self.me, command)
            replied = False
            starttime = time.time()
            triedreplicas = set()
            needreconfig = False
            lastcr = -1
            try:
                while not replied:
                    triedreplicas.add(self.bootstrap)
                    if lastcr != CR_BLOCK:
                        needreconfig = not self.conn.send(cm)

                    timestamp, reply = self.conn.receive()
                    if self.debug:
                        print "Received: %s" % str(reply)

                    if reply and reply.type == MSG_CLIENTREPLY and reply.inresponseto == mynumber:
                        if reply.replycode == CR_OK or reply.replycode == CR_EXCEPTION or reply.replycode == CR_UNBLOCK:
                            if reply.replycode == CR_UNBLOCK:
                                assert lastcr == CR_BLOCK, "unblocked thread not previously blocked"
                            lastcr = reply.replycode
                            replied = True
                        elif reply.replycode == CR_INPROGRESS or reply.replycode == CR_BLOCK:
                            # the thread is already in the loop, no need to do anything
                            lastcr = reply.replycode
                        elif reply.replycode == CR_REJECTED or reply.replycode == CR_LEADERNOTREADY:
                            needreconfig = True
                        else:
                            print "should not happen -- unknown response type"

                    while needreconfig:
                        if not self.trynewbootstrap(triedreplicas):
                            raise ConnectionError("Cannot connect to any bootstrap")
                        needreconfig = False
                        
            except KeyboardInterrupt:
                self._graceexit()

            if reply.replycode == CR_OK or reply.replycode == CR_UNBLOCK:
                print "Returning ", reply.reply
                return reply.reply
            elif reply.replycode == CR_EXCEPTION:
                raise Exception(reply.reply)
                
    def _graceexit(self):
        return
