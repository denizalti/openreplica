import socket
import select
from threading import Thread, Timer

from utils import *
from enums import *
from membership import *
from node import *
import dns.exception
import dns.message

DOMAIN = ['groups','openreplica','org','']

class Nameserver(Membership):
    """Nameserver keeps track of the connectivity state of the system and replies to
    QUERY messages from dnsserver."""
    def __init__(self):
        Membership.__init__(self, nodetype=NODE_NAMESERVER, port=5000, bootstrap=options.bootstrap)
        self.name = 'herbivore'
        self.registerednames = {'paxi':'127.0.0.1:5000'} # <name:nameserver> mappings
        self.nameserverconnections = {}  # <nameserver:connection> mappings

        self.udpport = 53 #DNS port: 53
        self.udpsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        try:
            self.udpsocket.bind((self.addr,self.udpport))
        except socket.error as e:
            print e
            print "Can't bind to UDP socket.."

    def startservice(self):
        """Starts the background services associated with a node."""
        Membership.startservice(self)
        # Start a thread for the UDP server
        UDP_server_thread = Thread(target=self.udp_server_loop)
        UDP_server_thread.start()
        
    # DNS Side
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
        #dnsmsg = DNSPacket(data)
        #query = dnsmsg.query
        query = dns.message.from_wire(data)
        response = dns.message.make_response(query)
        print "**QUERY**\n%s" % query
        print "!!", query.flags
        print "**RESPONSE**\n%s" % response
        print "!!", response.flags

        olek = "%0.4x" % dec
        olek.encode('hex_codec')


        for question in query.question:
            mydomain = dns.name.Name([self.name]+DOMAIN)
            if question.name == mydomain:
                print "This is me!"
                #response = query.create_a_response(peers, auth=True)
                self.udpsocket.sendto(response.to_wire(), addr)
            elif self.registerednames.has_key(question.name):
                print "Forwarding!"
                #response = query.create_ns_response(self.registerednames[question.name])
                self.udpsocket.sendto(response.to_wire(), addr)
            else:
                print "Error.."
                #response = query.create_error_response(self.addr)
        #print "**RESPONSE**\n%s" % response
        self.udpsocket.sendto(response.to_wire(), addr)

def main():
    nameservernode = Nameserver()
    nameservernode.startservice()

if __name__=='__main__':
    main()

## RRTYPE
# A               1 a host address
# NS              2 an authoritative name server
# CNAME           5 the canonical name for an alias
# SOA             6 marks the start of a zone of authority
## CLASS
# IN              1 the Internet
