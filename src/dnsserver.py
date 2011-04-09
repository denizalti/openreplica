#!/usr/bin/env python
import sys
import socket
import select
from optparse import OptionParser
from time import sleep,time


import dns.update
import dns.query
import dns.message

from utils import *

parser = OptionParser(usage="usage: %prog -p port -b bootstrap -d delay")
parser.add_option("-p", "--port", action="store", dest="port", type="int", default=6668, help="port for the node")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port:type triple for the bootstrap peer")

(options, args) = parser.parse_args()

# Find the address in question
# Connect to corresponding nameserver (TCP?)
# Get the list of members

class DNSServer():
    def __init__(self, port=options.port, bootstrap=options.bootstrap):
        self.addr = "127.0.0.1"
        self.port = port # DNS Port: 53
        self.registerednames = {'paxi':'127.0.0.1:5000'} # <name:nameserver> mappings

        # create server socket and bind to a port
        self.socket = socket.socket(AF_INET,SOCK_DGRAM)
            try:
                self.socket.bind((self.addr,self.port))
                break
            except socket.error:
                print "Can't bind to socket.."
        self.alive = True

    def server_loop():
        ip='192.168.1.1'
        try:
            while 1:
                data, addr = self.socket.recvfrom(1024)
                query = DNSQuery(data)
                self.socket.sendto(query.respond(ip), addr)
        except KeyboardInterrupt:
            self.socket.close()


    # To send a WHO message we will need a TCP Connection
    def msg_whoreply(self, conn, msg):
        """Send groups as a reply to the query msg"""
        pass
