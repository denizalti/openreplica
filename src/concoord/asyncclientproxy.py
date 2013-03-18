'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: ConCoord Client Proxy
@copyright: See LICENSE
'''
import socket, os, sys, time, random, threading, select
from threading import Thread, Condition, RLock, Lock
import pickle
from pack import *
from concoord.enums import *
from concoord.utils import *
from concoord.exception import *
from concoord.connection import ConnectionPool, Connection
from concoord.message import *
from concoord.pvalue import PValueSet
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
            self.commandnumber = clientproxy.commandnumber
            clientproxy.commandnumber += 1
        self.cm = create_message(MSG_CLIENTREQUEST, clientproxy.me,
                                 {FLD_PROPOSAL: Proposal(clientproxy.me, self.commandnumber, args), 
                                  FLD_TOKEN: token,
                                  FLD_SENDCOUNT: 0})
        self.starttime = time.time()
        self.replyarrived = False
        self.replyarrivedcond = Condition()
        self.lastreplycr = -1
        self.resendnecessary = False
        self.reply = None
        self.sendcount = 0

    def __str__(self):
        return "Request Descriptor for cmd %d\nMessage %s\nReply %s" % (self.commandnumber, str(self.cm), self.reply)

class ClientProxy():
    def __init__(self, bootstrap, timeout=60, debug=False, token=None):
        self.debug = debug
        self.timeout = timeout 
        self.domainname = None
        self.token = token
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.writelock = Lock()

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
        self.pendingops = {}
        self.reconfiglock = Lock()
        self.needreconfig = False

        # spawn thread, invoke recv_loop
        recv_thread = Thread(target=self.recv_loop, name='ReceiveThread')
        recv_thread.start()

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

    def invoke_command_async(self, *args):
        # create a request descriptor
        reqdesc = ReqDesc(self, args, self.token)
        # send the request
        success = self.conn.send(reqdesc.cm)
        if not success:
            with self.reconfiglock:
                self.needreconfig = True
        with self.lock:
            self.pendingops[reqdesc.commandnumber] = reqdesc
        # Do not wait for the reply, return the reqdesc
        return reqdesc

    def recv_loop(self, *args):
        try:
            triedreplicas = set()
            while True:
                triedreplicas.add(self.bootstrap)
                try:
                    for reply in self.conn.received_bytes():
                        if reply and reply.type == MSG_CLIENTREPLY:
                            # received a reply
                            reqdesc = self.pendingops[reply.inresponseto]
                            if reply.replycode == CR_OK or reply.replycode == CR_EXCEPTION or \
                                    reply.replycode == CR_UNBLOCK:
                                # actionable response, wake up the thread
                                if reply.replycode == CR_UNBLOCK:
                                    assert reqdesc.lastcr == CR_BLOCK, "unblocked thread not previously blocked"
                                reqdesc.lastcr = reply.replycode
                                reqdesc.reply = reply
                                reqdesc.replyarrived = True
                                reqdesc.replyarrivedcond.notify()
                            elif reply.replycode == CR_INPROGRESS or reply.replycode == CR_BLOCK:
                                # the thread is already waiting, no need to do anything
                                reqdesc.lastcr = reply.replycode
                            elif reply.replycode == CR_REJECTED or reply.replycode == CR_LEADERNOTREADY:
                                reqdesc.replyarrived = True
                                reqdesc.resendnecessary = True
                                reqdesc.replyarrivedcond.notify()                                
                                with self.reconfiglock:
                                    self.needreconfig = True
                            else:
                                print "should not happen -- unknown response type"
                except:
                    with self.reconfiglock:
                        self.needreconfig = True

                with self.reconfiglock:
                    while self.needreconfig:
                        if not self.trynewbootstrap(triedreplicas):
                            raise ConnectionError("Cannot connect to any bootstrap")
                        self.needreconfig = False
                        continue

        except KeyboardInterrupt:
            self._graceexit()

    def wait_until_command_done(self, reqdesc):
        if reqdesc.reply.replycode == CR_OK or reqdesc.reply.replycode == CR_UNBLOCK:
            return reqdesc.reply.reply
        elif reqdesc.reply.replycode == CR_EXCEPTION:
            raise Exception(reqdesc.reply.reply)
        else:
            return "Unexpected Client Reply Code: %d" % reqdesc.reply.replycode

    def _graceexit(self):
        os._exit(0)
