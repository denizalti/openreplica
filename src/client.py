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

parser = OptionParser(usage="usage: %prog -b bootstrap -f file -n serverdomainname -d debug")
parser.add_option("-b", "--bootstrap", action="store", dest="bootstrap", help="address:port tuples separated with commas for bootstrap peers")
parser.add_option("-f", "--file", action="store", dest="filename", default=None, help="inputfile")
parser.add_option("-n", "--name", action="store", dest="name", default=None, help="domain name of the concoord instance")
parser.add_option("-d", "--debug", action="store_true", dest="debug", default=False, help="debug on/off")
(options, args) = parser.parse_args()

class Client():
    """Client sends requests and receives responses"""
    def __init__(self, givenbootstraplist, inputfile, debug, domainname):
        self.servicedomainname = domainname
        self.bootstraplist = []
        self.debug = debug
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.socket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        # XXX When we have the DNS running we won't need this function
        self.initializebootstraplist(givenbootstraplist)
        self.connecttobootstrap()
        myaddr = findOwnIP()
        myport = self.socket.getsockname()[1] 
        self.me = Peer(myaddr,myport,NODE_CLIENT)
        self.alive = True
        self.clientcommandnumber = 1
        self.file = inputfile
        
    def initializebootstraplist(self, givenbootstraplist):
        bootstrapstrlist = givenbootstraplist.split(",")
        for bootstrap in bootstrapstrlist:
            bootaddr,bootport = bootstrap.split(":")
            for node in self.socket.getaddrinfo(bootaddr, int(bootport)):
                bootpeer = Peer(node[4][0],int(bootport),NODE_REPLICA)
                self.bootstraplist.append(bootpeer)

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
    
    def clientloop(self):
        """Accepts commands from the prompt and sends requests for the commands
        and receives corresponding replies."""
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
                            currentbootstrap = self.bootstraplist.pop(0)
                            self.bootstraplist.append(currentbootstrap)
                            self.connecttobootstrap()
                            continue
                        try:
                            timestamp, reply = self.conn.receive()
                        except KeyboardInterrupt:
                            self.graceexit()
                        if reply and (reply.type == MSG_CLIENTREPLY or reply.type == MSG_CLIENTMETAREPLY) and reply.inresponseto == mynumber:
                            if reply.replycode == CR_REJECTED or reply.replycode == CR_LEADERNOTREADY:
                                currentbootstrap = self.bootstraplist.pop(0)
                                self.bootstraplist.append(currentbootstrap)
                                self.connecttobootstrap()
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
                        sys.stdout.flush()
            except ( IOError, EOFError ):
                self.graceexit()
            except KeyboardInterrupt:
                self.graceexit()

    def terminate_handler(self, signal, frame):
        self.graceexit()
        
    def graceexit(self):
        if self.debug:
            print "Exiting.."
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)

        
theClient = Client(options.bootstrap, options.filename, options.name, options.debug)
theClient.clientloop()
signal.signal(signal.SIGINT, theClient.terminate_handler)
signal.signal(signal.SIGTERM, theClient.terminate_handler)
signal.pause()

  


    
