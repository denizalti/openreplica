import socket
import select
from optparse import OptionParser
from threading import Thread, Timer

from utils import *
from enums import *
from node import Node, options
from dnsquery import DNSQuery, DNSPacket

class Nameserver(Node):
    """Nameserver keeps track of the connectivity state of the system and replies to
    QUERY messages from dnsserver."""
    def __init__(self):
        Node.__init__(self, NODE_NAMESERVER, port=5000,  bootstrap=options.bootstrap)
        self.name = 'herbivore'
        self.registerednames = {'paxi':'127.0.0.1:5000'} # <name:nameserver> mappings
        self.nameserverconnections = {}  # <nameserver:connection> mappings

        self.udpport = 10000 #DNS port: 53
        self.udpsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        try:
            self.udpsocket.bind((self.addr,self.udpport))
        except socket.error:
            print "Can't bind to UDP socket.."

    def startservice(self):
        """Starts the background services associated with a node."""
        # Start a thread for the TCP server
        TCP_server_thread = Thread(target=self.server_loop)
        TCP_server_thread.start()
        # Start a thread for the UDP server
        UDP_server_thread = Thread(target=self.udp_server_loop)
        UDP_server_thread.start()
        # Start a thread that pings neighbors
        timer_thread = Timer(ACKTIMEOUT/5, self.periodic)
        timer_thread.start()

    def udp_server_loop(self):
        while self.alive:
            try:
                print "Waiting..."
                inputready,outputready,exceptready = select.select([self.udpsocket],[],[self.udpsocket])
                for s in exceptready:
                    print "EXCEPTION ", s
                for s in inputready:
                    data,clientaddr = self.udpsocket.recvfrom(UDPMAXLEN)
                    logger("received a message from address %s" % str(clientaddr))
                    self.handle_query(data,clientaddr)
            except KeyboardInterrupt, EOFError:
                os._exit(0)
        self.udpsocket.close()
        return

    def handle_query(self, data, addr):
        dnsmsg = DNSPacket(data)
        query = dnsmsg.query
        serializedgroups = ""
        for group in self.groups:
            serializedgroups += group.serialize()
        if query.domain == self.name:
            response = query.create_a_response(serializedgroups)
            self.udpsocket.sendto(response, addr)
        elif self.registerednames.has_key(query.domain):
            response = query.create_ns_response(self.registerednames[query.domain])
            self.udpsocket.sendto(response, addr)
        else:
            response = query.create_error_response()
            self.udpsocket.sendto(response, addr)

# nameserver query function
    def msg_query(self, conn, msg):
        """Send groups as a reply to the query msg"""
        serializedgroups = ""
        for group in self.groups:
            serializedgroups += group.serialize()
        queryreplymessage = HandshakeMessage(MSG_QUERYREPLY, self.me, serializedgroups)
        self.send(queryreplymessage, peer=msg.source)

def main():
    nameservernode = Nameserver()
    nameservernode.startservice()

if __name__=='__main__':
    main()
