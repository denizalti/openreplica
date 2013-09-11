'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: ConCoord Client Proxy
@copyright: See LICENSE
'''
import os, random, select, socket, sys, threading, time
import cPickle as pickle
from threading import Thread, Condition, Lock
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
        with clientproxy.lock:
            # acquire a unique command number
            self.commandnumber = clientproxy.commandnumber
            clientproxy.commandnumber += 1
        self.cm = create_message(MSG_CLIENTREQUEST, clientproxy.me,
                                 {FLD_PROPOSAL: Proposal(clientproxy.me, self.commandnumber, args),
                                  FLD_TOKEN: token,
                                  FLD_CLIENTBATCH: False,
                                  FLD_SENDCOUNT: 0})
        self.starttime = time.time()
        self.replyarrived = Condition(clientproxy.lock)
        self.lastreplycr = -1
        self.replyvalid = False
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
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket.setblocking(1)
        self.writelock = Lock()

        self.bootstraplist = self.discoverbootstrap(bootstrap)
        if len(self.bootstraplist) == 0:
            raise ConnectionError("No bootstrap found")
        if not self.connecttobootstrap():
            raise ConnectionError("Cannot connect to any bootstrap")
        myaddr = findOwnIP()
        myport = self.socket.getsockname()[1]
        self.me = Peer(myaddr, myport, NODE_CLIENT)
        self.commandnumber = random.randint(1, sys.maxint)

        # synchronization
        self.lock = Lock()
        self.pendingops = {}  # pending requests indexed by commandnumber
        self.doneops = {}  # requests that are finalized, indexed by command number

        # spawn thread, invoke recv_loop
        try:
            recv_thread = Thread(target=self.recv_loop, name='ReceiveThread')
            recv_thread.daemon = True
            recv_thread.start()
        except (KeyboardInterrupt, SystemExit):
            self._graceexit()

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
            if self.debug: print "Cannot resolve name"
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
            if self.debug: print "bootstrap usage: ipaddr1:port1,ipaddr2:port2 or domainname"
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
                if self.debug: print "Connected to new bootstrap: ", boottuple
                break
            except socket.error, e:
                if self.debug: print "Socket.Error: ", e
                continue
        return connected

    def trynewbootstrap(self):
        if self.domainname:
            self.bootstraplist = self.getbootstrapfromdomain(self.domainname)
        else:
            oldbootstrap = self.bootstraplist.pop(0)
            self.bootstraplist.append(oldbootstrap)
        return self.connecttobootstrap()

    def invoke_command(self, *args):
        # create a request descriptor
        reqdesc = ReqDesc(self, args, self.token)
        self.pendingops[reqdesc.commandnumber] = reqdesc
        # send the request
        with self.writelock:
            self.conn.send(reqdesc.cm)
        with self.lock:
            try:
                while not reqdesc.replyvalid:
                    reqdesc.replyarrived.wait()
            except KeyboardInterrupt:
                self._graceexit()
            del self.pendingops[reqdesc.commandnumber]
        if reqdesc.reply.replycode == CR_OK or reqdesc.reply.replycode == CR_UNBLOCK:
            return reqdesc.reply.reply
        elif reqdesc.reply.replycode == CR_EXCEPTION:
            raise Exception(pickle.loads(reqdesc.reply.reply))
        else:
            print "Unexpected Client Reply Code: %d" % reqdesc.reply.replycode

    def recv_loop(self, *args):
        socketset = [self.socket]
        while True:
            try:
                needreconfig = False
                inputready,outputready,exceptready = select.select(socketset, [], socketset, 0)
                for s in inputready:
                    reply = self.conn.receive()
                    if reply is None:
                        needreconfig = True
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
                    if not self.trynewbootstrap():
                        raise ConnectionError("Cannot connect to any bootstrap")
                    needreconfig = False

                    # check if we need to re-send any pending operations
                    for commandno,reqdesc in self.pendingops.iteritems():
                        if not reqdesc.replyvalid and reqdesc.lastreplycr != CR_BLOCK:
                            reqdesc.sendcount += 1
                            reqdesc.cm[FLD_SENDCOUNT] = reqdesc.sendcount
                            if not self.conn.send(reqdesc.cm):
                                needreconfig = True
                            continue
            except KeyboardInterrupt:
                self._graceexit()

    def _graceexit(self):
        os._exit(0)
