'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: ConCoord Client Proxy
@copyright: See LICENSE
'''
import socket, os, sys, time, random, threading
from threading import Thread, Lock, Condition
from concoord.enums import *
from concoord.utils import *
from concoord.connection import ConnectionPool, Connection
from concoord.group import Group
from concoord.peer import Peer
from concoord.message import ClientMessage, Message, PaxosMessage, HandshakeMessage, AckMessage
from concoord.command import Command
from concoord.pvalue import PValue, PValueSet
try:
    from openreplicasecret import LOGGERNODE
except:
    print "To turn on Logging through the Network, edit NetworkLogger credentials"
    LOGGERNODE = '128.84.154.110:12000'
try:
    import dns
    import dns.resolver
    import dns.exception
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
                print "No bootstrap found!"
            self._graceexit()
        self.connecttobootstrap()
        myaddr = findOwnIP()
        myport = self.socket.getsockname()[1]
        self.me = Peer(myaddr,myport,NODE_CLIENT)
        self.logger = NetworkLogger("%s-%s" % ('NODE_CLIENT',self.me.getid()), LOGGERNODE)
        self.commandnumber = random.randint(1, sys.maxint)
        self.lock = Lock()

    def _getipportpairs(self, bootaddr, bootport):
        for node in socket.getaddrinfo(bootaddr, bootport):
            yield Peer(node[4][0],bootport,NODE_REPLICA)

    def _getbootstrapfromdomain(self, domainname):
        try:
            r = dns.resolver.Resolver()
            r.nameservers.append('127.0.0.1')
            answers = r.query('_concoord._tcp.'+domainname, 'SRV')
            for rdata in answers:
                for peer in self._getipportpairs(str(rdata.target), rdata.port):
                    yield peer
        except (dns.resolver.NXDOMAIN, dns.exception.Timeout):
            print "Cannot resolve name."

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
                self.bootstrap = bootpeer.addr,bootpeer.port
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
                    if time.time() - starttime > CLIENTRESENDTIMEOUT:
                        if self.debug:
                            print "Timed out: %d seconds" % CLIENTRESENDTIMEOUT
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
                        self._trynewbootstrap()
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
  


    
