'''
@author: denizalti
@note: The Client
@date: February 1, 2011
'''
import socket, os, sys, time, signal
from optparse import OptionParser
from peer import Peer
from enums import *
from utils import findOwnIP
from connection import ConnectionPool, Connection
from group import Group
from message import ClientMessage, Message, PaxosMessage, HandshakeMessage, AckMessage
from command import Command
from pvalue import PValue, PValueSet
try:
    import dns.resolver
except:
    logger("Install dnspython: http://www.dnspython.org/")

parser = OptionParser(usage="usage: %prog -b bootstrap -f file -n name -d debug")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="bootstrap ipaddr:port list or server domain name")
parser.add_option("-f", "--file", action="store", dest="filename", default=None, help="inputfile")
parser.add_option("-d", "--debug", action="store_true", dest="debug", default=False, help="debug on/off")
(options, args) = parser.parse_args()

class Client():
    """Client sends requests and receives responses"""
    def __init__(self, bootstrap, inputfile, debug):
        self.debug = debug
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.socket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        self.bootstraplist = []
        self.domainname = None
        self.discoverbootstrap(bootstrap)
        self.connecttobootstrap()
        myaddr = findOwnIP()
        myport = self.socket.getsockname()[1] 
        self.me = Peer(myaddr,myport,NODE_CLIENT)
        self.alive = True
        self.clientcommandnumber = 1
        self.file = inputfile

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
    
    def clientloop(self):
        # Read commands from a file
        if self.file:
            f = open(self.file,'r')
            EOF = False
            if self.debug:
                print "Reading inputs from %s" % self.file
        # Read commands from the shell
        while self.alive:
            try:
                if self.file and not EOF:
                    shellinput = f.readline().strip()
                else:
                    shellinput = raw_input("client$ ")
                    
                if len(shellinput) == 0:
                    if self.file:
                        EOF = True
                    continue
                else:
                    mynumber = self.clientcommandnumber
                    self.clientcommandnumber += 1
                    command = Command(self.me, mynumber, shellinput)
                    if self.debug:
                        print "Initiating command %s" % str(command)
                    cm = ClientMessage(MSG_CLIENTREQUEST, self.me, command)
                    replied = False
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
                        if reply and (reply.type == MSG_CLIENTREPLY or reply.type == MSG_CLIENTMETAREPLY) and reply.inresponseto == mynumber:
                            if reply.replycode == CR_REJECTED or reply.replycode == CR_LEADERNOTREADY:
                                self._trynewbootstrap()
                                continue
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
                self._graceexit()
            except KeyboardInterrupt:
                self._graceexit()

    def terminate_handler(self, signal, frame):
        self._graceexit()
        
    def _graceexit(self):
        if self.debug:
            print "Exiting.."
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)

        
theClient = Client(options.bootstrap, options.filename, options.debug)
theClient.clientloop()
signal.signal(signal.SIGINT, theClient.terminate_handler)
signal.signal(signal.SIGTERM, theClient.terminate_handler)
signal.pause()

  


    
