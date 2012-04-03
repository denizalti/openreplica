'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: ConCoord Client Proxy
@copyright: See LICENSE
'''
import socket, os, sys, time, random, threading
from threading import Thread, Lock, Condition
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
    def __init__(self, bootstrap, timeout=60, debug=False):
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
            argstuple = args
            command = Command(self.me, mynumber, argstuple)
            cm = ClientMessage(MSG_CLIENTREQUEST, self.me, command)
            replied = False
            if self.debug:
                print "Initiating command %s" % str(command)
            starttime = time.time()
            try:
                self.conn.settimeout(CLIENTRESENDTIMEOUT)
            except:
                return "Cannot connect to object"
            triedreplicas = set()
            while not replied:
                triedreplicas.add(self.bootstrap)
                try:
                    success = self.conn.send(cm)
                    if self.debug:
                        print "Bootstrap: ", self.bootstrap
                        print "Sent: %s" % str(cm)
                    if not success:
                        raise IOError
                    timestamp, reply = self.conn.receive()
                    if self.debug:
                        print "Received: %s" % str(reply)
                    if reply and reply.type == MSG_CLIENTREPLY and reply.inresponseto == mynumber:
                        if reply.replycode == CR_REJECTED or reply.replycode == CR_LEADERNOTREADY:
                            raise IOError
                        elif reply.replycode == CR_INPROGRESS:
                            continue
                        else:
                            replied = True
                    timecheck = time.time() - starttime
                    if timecheck > CLIENTRESENDTIMEOUT:
                        if self.debug:
                            print "Timed out: %d seconds" % CLIENTRESENDTIMEOUT
                        if reply and reply.type == MSG_CLIENTREPLY and reply.inresponseto == mynumber:
                            replied = True
                        if not replied and timecheck > self.timeout:
                            if self.debug:
                                print "Connection timed out"
                            raise IOError
                except (IOError, EOFError):
                    if not self.trynewbootstrap(triedreplicas):
                        raise ConnectionError("Cannot connect to any bootstrap")
                except KeyboardInterrupt:
                    self._graceexit()
            if reply.replycode == CR_META:
                return
            elif reply.replycode == CR_EXCEPTION:
                raise Exception(reply.reply)
            elif reply.replycode == CR_BLOCK:
                # Wait until an UNBLOCK msg is received
                replied = False
                while not replied:
                    try:
                        timestamp, reply = self.conn.receive()
                        if self.debug:
                            print "Received:  %s" % str(reply)
                        if reply and reply.type == MSG_CLIENTREPLY and reply.inresponseto == mynumber:
                            if reply.replycode == CR_REJECTED or reply.replycode == CR_LEADERNOTREADY:
                                raise IOError
                            elif reply.replycode == CR_INPROGRESS:
                                continue
                            else:
                                replied = True
                    except ( IOError, EOFError ):
                        if not self.trynewbootstrap(triedreplicas):
                            raise ConnectionError("Cannot connect to any bootstrap")
                    except KeyboardInterrupt:
                        self._graceexit()
                if reply.replycode == CR_UNBLOCK:
                    return
            elif reply.replycode == CR_UNBLOCK:
                return    
            else:
                return reply.reply
            
    def _graceexit(self):
        return
  


    
