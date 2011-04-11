#!/usr/bin/env python
import sys
import socket
import select
from optparse import OptionParser
from time import sleep,time
from utils import *
from dnsquery import DNSQuery

parser = OptionParser(usage="usage: %prog -p port -b bootstrap")
parser.add_option("-p", "--port", action="store", dest="port", type="int", default=10000, help="port for the dnsserver")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port:type triple for the bootstrap peer")

(options, args) = parser.parse_args()

# Find the address in question
# Connect to corresponding nameserver (TCP?)
# Get the list of members

MAXLEN = 1024

class DNSServer():
    def __init__(self, port=options.port, bootstrap=options.bootstrap):
        self.addr = "127.0.0.1"
        self.port = port # DNS Port: 53
        self.registerednames = {'paxi':'127.0.0.1:5000'} # <name:nameserver> mappings
        self.nameserverconnections = {}  # <nameserver:connection> mappings

        # create server socket and bind to a port
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        try:
            self.socket.bind((self.addr,self.port))
        except socket.error:
            print "Can't bind to socket.."
        self.alive = True
        setlogprefix("%s %s:%d" % ("DNSSERVER",self.addr,self.port))
        logger("Running!")
        self.server_loop()

    def server_loop(self):
        while self.alive:
            try:
                print "Waiting..."
                inputready,outputready,exceptready = select.select([self.socket],[],[self.socket])
                for s in exceptready:
                    print "EXCEPTION ", s
                for s in inputready:
                    data,clientaddr = self.socket.recvfrom(MAXLEN)
                    logger("received a message from address %s" % str(clientaddr))
                    self.handle_query(data,clientaddr)

            except KeyboardInterrupt, EOFError:
                os._exit(0)
        self.socket.close()
        return

    def handle_query(self, data, addr):
        query = DNSQuery(data)
        print "QUERY for ", query.domain
#        self.socket.sendto(XXX, addr)

    # To send a WHO message we will need a TCP Connection
    def msg_queryreply(self, conn, msg):
        """Send the groups in the message as a reply to the DNSQuery"""
        peers = msg.peers.split()
        for peer in peers:
            print peer

def main():
    nameservernode = DNSServer()
    nameservernode.startservice()

if __name__=='__main__':
    main()        
