'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: ConCoord Client Proxy
@copyright: See LICENSE
'''
import socket, os, sys, time, random, threading, select
from threading import Thread, Condition, RLock, Lock
import pickle
from concoord.enums import *
from concoord.utils import *
from concoord.exception import *
from concoord.connection import ConnectionPool, Connection
from concoord.group import Group
from concoord.peer import Peer
from concoord.message import ClientMessage, Message, PaxosMessage, HandshakeMessage
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

class ReqDesc:
    def __init__(self, clientproxy, args, token):
        with clientproxy.lock:
            # acquire a unique command number
            self.mynumber = clientproxy.commandnumber
            clientproxy.commandnumber += 1
        self.cm = ClientMessage(MSG_CLIENTREQUEST, clientproxy.me, Command(clientproxy.me, self.mynumber, args), token=token)
        self.starttime = time.time()
        self.replyarrived = Condition(clientproxy.lock)
        self.lastreplycr = -1
        self.replyvalid = False
        self.reply = None

    def __str__(self):
        return "Request Descriptor for cmd %d\nMessage %s\nReply %s" % (self.mynumber, self.cm, self.reply)

class ClientProxy():
    def __init__(self, bootstrap, timeout=60, debug=False, token=None):
        self.debug = debug
        self.timeout = timeout 
        self.domainname = None
        self.token = token
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

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
        self.lock = RLock()
        self.ctrlsockets, self.ctrlsocketr = socket.socketpair()
        self.reqlist = []     # requests we have received from client threads
        self.pendingops = {}  # pending requests indexed by command number

        # spawn thread, invoke comm_loop
        comm_thread = Thread(target=self.comm_loop, name='CommunicationThread')
        comm_thread.start()

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
        # create a request descriptor
        reqdesc = ReqDesc(self, args, self.token)
        with self.lock:
            # append the request descriptor to the list of requests
            self.reqlist.append(reqdesc)
            self.ctrlsockets.send('a')
            while not reqdesc.replyvalid:
                reqdesc.replyarrived.wait()
            del self.pendingops[reqdesc.mynumber]
        if reqdesc.reply.replycode == CR_OK or reqdesc.reply.replycode == CR_UNBLOCK:
            return reqdesc.reply.reply
        elif reqdesc.reply.replycode == CR_EXCEPTION:
            raise Exception(reqdesc.reply.reply)
        else:
            print "should not happen -- client thread saw reply code %d" % reqdesc.reply.replycode

    def comm_loop(self, *args):
        try:
            triedreplicas = set()
            while True:
                triedreplicas.add(self.bootstrap)
                socketset = [self.ctrlsocketr, self.conn.thesocket]
                inputready,outputready,exceptready = select.select(socketset,[],socketset,0)
                
                needreconfig = False
                for s in exceptready:
                    print "EXCEPTION ", s
                for s in inputready:
                    if s == self.ctrlsocketr:
                        # a local thread has queued up a request and needs our attention
                        self.ctrlsocketr.recv(1)
                        with self.lock:
                            while len(self.reqlist) > 0:
                                reqdesc = self.reqlist.pop(0)
                                self.pendingops[reqdesc.mynumber] = reqdesc
                                needreconfig = not self.conn.send(reqdesc.cm)
                    else:
                        # server has sent us something and we need to process it
                        reply = self.conn.receive()
                        if reply is None:
                            needreconfig = True
                            print "CAUGHT!"
                        elif reply and reply.type == MSG_CLIENTREPLY:
                            reqdesc = self.pendingops[reply.inresponseto]
                            with self.lock:
                                if reply.replycode == CR_OK or reply.replycode == CR_EXCEPTION or reply.replycode == CR_UNBLOCK:
                                    # actionable response, wake up the thread
                                    if reply.replycode == CR_UNBLOCK:
                                        assert reqdesc.lastcr == CR_BLOCK, "unblocked thread not previously blocked"
                                    reqdesc.lastcr = reply.replycode
                                    reqdesc.reply = reply
                                    reqdesc.replyvalid = True
                                    reqdesc.replyarrived.notify()
                                elif reply.replycode == CR_INPROGRESS or reply.replycode == CR_BLOCK:
                                    # the thread is already waiting, no need to do anything
                                    reqdesc.lastcr = reply.replycode
                                elif reply.replycode == CR_REJECTED or reply.replycode == CR_LEADERNOTREADY:
                                    needreconfig = True
                                else:
                                    print "should not happen -- unknown response type"

                while needreconfig:
                    if not self.trynewbootstrap(triedreplicas):
                        raise ConnectionError("Cannot connect to any bootstrap")
                    needreconfig = False

                    # check if we need to re-send any pending operations
                    print "GOING THROUGH..."
                    for commandno,reqdesc in self.pendingops.iteritems():
                        print commandno, ": ", str(reqdesc)
                        if not reqdesc.replyvalid and reqdesc.lastreplycr != CR_BLOCK: # XXX CR_INPROGRESS?
                            if not self.conn.send(reqdesc.cm):
                                needreconfig = True
                            continue

        except KeyboardInterrupt:
            self._graceexit()
            
    def _graceexit(self):
        return
  


    
