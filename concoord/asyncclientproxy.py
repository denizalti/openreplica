'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: ConCoord Client Proxy
@copyright: See LICENSE
'''
import socket, os, sys, time, random, threading, select
from threading import Thread, Condition, RLock, Lock
import pickle
from concoord.pack import *
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

class ReqDesc:
    def __init__(self, clientproxy, args, token):
        # acquire a unique command number
        self.commandnumber = clientproxy.commandnumber
        clientproxy.commandnumber += 1
        self.cm = create_message(MSG_CLIENTREQUEST, clientproxy.me,
                                 {FLD_PROPOSAL: Proposal(clientproxy.me, self.commandnumber, args),
                                  FLD_TOKEN: token,
                                  FLD_CLIENTBATCH: False,
                                  FLD_SENDCOUNT: 0})
        self.reply = None
        self.replyarrived = False
        self.replyarrivedcond = Condition()
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
        self.writelock = Lock()
        self.needreconfig = False
        self.outstanding = []

        # spawn thread, invoke recv_loop
        recv_thread = Thread(target=self.recv_loop, name='ReceiveThread')
        recv_thread.start()

    def _getipportpairs(self, bootaddr, bootport):
        for node in socket.getaddrinfo(bootaddr, bootport, socket.AF_INET, socket.SOCK_STREAM):
            yield (node[4][0],bootport)

    def getbootstrapfromdomain(self, domainname):
        tmpbootstraplist = []
        try:
            answers = dns.resolver.query('_concoord._tcp.'+domainname, 'SRV')
            for rdata in answers:
                for peer in self._getipportpairs(str(rdata.target), rdata.port):
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
                bootstrap = bootstrap.strip()
                # The bootstrap list is read only during initialization
                if bootstrap.find(":") >= 0:
                    bootaddr,bootport = bootstrap.split(":")
                    for peer in self._getipportpairs(bootaddr, int(bootport)):
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

    def trynewbootstrap(self):
        if self.domainname:
            self.bootstraplist = self.getbootstrapfromdomain(self.domainname)
        else:
            oldbootstrap = self.bootstraplist.pop(0)
            self.bootstraplist.append(oldbootstrap)
        return self.connecttobootstrap()

    def invoke_command_async(self, *args):
        # create a request descriptor
        reqdesc = ReqDesc(self, args, self.token)
        # send the clientrequest
        with self.writelock:
            success = self.conn.send(reqdesc.cm)
            self.pendingops[reqdesc.commandnumber] = reqdesc
            # if the message is not sent, we should reconfigure
            # and send it without making the client wait
            if not success:
                self.outstanding.append(reqdesc)
            self.needreconfig = not success
        return reqdesc

    def wait_until_command_done(self, reqdesc):
        with reqdesc.replyarrivedcond:
            while not reqdesc.replyarrived:
                reqdesc.replyarrivedcond.wait()
        if reqdesc.reply.replycode == CR_OK:
            return reqdesc.reply.reply
        elif reqdesc.reply.replycode == CR_EXCEPTION:
            raise Exception(reqdesc.reply.reply)
        else:
            return "Unexpected Client Reply Code: %d" % reqdesc.reply.replycode

    def recv_loop(self, *args):
        while True:
            try:
                for reply in self.conn.received_bytes():
                    if reply and reply.type == MSG_CLIENTREPLY:
                        # received a reply
                        reqdesc = self.pendingops[reply.inresponseto]
                        # Async Clientproxy doesn't support BLOCK and UNBLOCK
                        if reply.replycode == CR_OK or reply.replycode == CR_EXCEPTION:
                            # the request is done
                            reqdesc.reply = reply
                            with reqdesc.replyarrivedcond:
                                reqdesc.replyarrived = True
                                reqdesc.replyarrivedcond.notify()
                            del self.pendingops[reply.inresponseto]
                        elif reply.replycode == CR_INPROGRESS:
                            # the request is not done yet
                            pass
                        elif reply.replycode == CR_REJECTED or reply.replycode == CR_LEADERNOTREADY:
                            # the request should be resent after reconfiguration
                            with self.lock:
                                self.outstanding.append(reqdesc)
                                self.needreconfig = True
                        else:
                            print "Unknown Client Reply Code"
            except ConnectionError:
                self.needreconfig = True
            except KeyboardInterrupt:
                self._graceexit()

            with self.lock:
                if self.needreconfig:
                    if not self.trynewbootstrap():
                        raise ConnectionError("Cannot connect to any bootstrap")

            with self.writelock:
                for reqdesc in self.outstanding:
                    success = self.conn.send(reqdesc.cm)
                    if success:
                        self.outstanding.remove(reqdesc)

    def _graceexit(self):
        os._exit(0)
