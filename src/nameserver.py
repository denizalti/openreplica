import socket
import select
from threading import Thread, Timer

from utils import *
from enums import *
from membership import *
from node import *
import dns.exception
import dns.message
import dns.rcode
import dns.opcode
import dns.rdatatype
import dns.name
from dns.flags import *

DOMAIN = ['groups','openreplica','org','']
RRTYPE = ['','A','NS','MD','MF','CNAME','SOA']
RRCLASS = ['','IN','CS','CH','HS']
OPCODES = ['QUERY','IQUERY','STATUS']
RCODES = ['NOERROR','FORMERR','SERVFAIL','NXDOMAIN','NOTIMP','REFUSED']

class Nameserver(Membership):
    """Nameserver keeps track of the connectivity state of the system and replies to
    QUERY messages from dnsserver."""
    def __init__(self):
        Membership.__init__(self, nodetype=NODE_NAMESERVER, port=5000, bootstrap=options.bootstrap)
        self.name = dns.name.Name(['herbivore']+DOMAIN)
        self.registerednames = {dns.name.Name(['paxi']+DOMAIN):'127.0.0.1'} # <name:nameserver> mappings
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
        query = dns.message.from_wire(data)
        response = dns.message.make_response(query)
        print "**QUERY**\n%s" % query
        print "**RESPONSE**\n%s" % response

#        flags = "%0.4x" % flagsdec
#        flags = flags.decode('hex_codec')

        for question in query.question:
            if question.name.parent() != self.name.parent():
                print "Format Error"
                # Which Flags to set?
                # QR : this is a response
                # AA : I'm an authority as I know all nameservers in the system
                # RD : *recursion* comes from the query
                # RCODE : 1 (Format Error)
                flags = QR + AA + RD + dns.rcode.FORMERR
                response.flags = flags
                print "**RESPONSE**\n%s" % response
            elif question.name == self.name:
                print "This is me."
                # Which Flags to set?
                # QR : this is a response
                # AA : as this is me I'm an authority
                # RD : *recursion* comes from the query
                # RA ? Support for Recursion
                # RCODE : 0 (No Error)
                flagstr = 'QR AA RD'
                answerstr = self.create_answer_section(question, addr='1.2.3.4')
                responsestr = self.create_response(response.id,opcode=dns.opcode.QUERY,rcode=dns.rcode.NOERROR,flags=flagstr,question=question.to_text(),answer=answerstr,authority='',additional='')
                print responsestr
                response = dns.message.from_text(responsestr)
            elif self.registerednames.has_key(question.name):
                print "Forwarding"
                # Which Flags to set?
                # QR : this is a response
                # RD : *recursion* comes from the query
                # RA ? Support for Recursion
                # RCODE : 0 (No Error)
                flagstr = 'QR RD'
                answerstr = self.create_answer_section(question, rrtype=dns.rdatatype.NS, name=str(question.name))
                responsestr = self.create_response(response.id,opcode=dns.opcode.QUERY,rcode=dns.rcode.NOERROR,flags=flagstr,question=question.to_text(),answer=answerstr,authority='',additional='')
                response = dns.message.from_text(responsestr)
            else:
                print "Name Error"
                # Which Flags to set?
                # QR : this is a response
                # AA : I'm an authority as I know all nameservers in the system
                # RD : *recursion* comes from the query
                # RCODE : 3 (Name Error)
                flags = QR + AA + RD + dns.rcode.NXDOMAIN
                response.flags = flags
        #print "**RESPONSE**\n%s" % response
        self.udpsocket.sendto(response.to_wire(), addr)

    def create_response(self, id, opcode=0, rcode=0, flags='', question='', answer='', authority='', additional=''):
        responsestr = "id %s\nopcode %s\nrcode %s\nflags %s\n;QUESTION\n%s\n;ANSWER\n%s\n;AUTHORITY\n%s\n;ADDITIONAL\n%s\n" % (str(id), OPCODES[opcode], RCODES[rcode], flags, question, answer, authority, additional)
        return responsestr

    def create_answer_section(self, question, ttl='3600', rrclass=1, rrtype=1, addr='', name=''):
        if rrtype == dns.rdatatype.A:
            answerstr = str(question.name) + ' ' + ttl + ' ' + RRCLASS[rrclass] + ' ' + RRTYPE[rrtype] + ' ' + addr
        elif rrtype == dns.rdatatype.NS:
            answerstr = str(question.name) + ' ' + ttl + ' ' + RRCLASS[rrclass] + ' ' + RRTYPE[rrtype] + ' ' + name
        return answerstr
        
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
