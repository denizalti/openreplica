import socket
import select
from threading import Thread, Timer
from time import strftime
import signal

from utils import *
from enums import *
from tracker import *
from node import *
try:
    import dns.exception
    import dns.message
    import dns.rcode
    import dns.opcode
    import dns.rdatatype
    import dns.name
    from dns.flags import *
except:
    logger("Install dnspython: http://www.dnspython.org/")

RRTYPE = ['','A','NS','MD','MF','CNAME','SOA', 'MB', 'MG', 'MR', 'NULL', 'WKS', 'PTR', 'HINFO', 'MINFO', 'MX', 'TXT', 'RP']
RRCLASS = ['','IN','CS','CH','HS']
OPCODES = ['QUERY','IQUERY','STATUS']
RCODES = ['NOERROR','FORMERR','SERVFAIL','NXDOMAIN','NOTIMP','REFUSED']

class Nameserver(Tracker):
    """Nameserver keeps track of the connectivity state of the system and replies to
    QUERY messages from dnsserver."""
    def __init__(self, domain):
        Tracker.__init__(self, nodetype=NODE_NAMESERVER, port=5000, bootstrap=options.bootstrap)
        self.mydomain = dns.name.Name((domain+".").split("."))
        self.udpport = 53
        self.udpsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        try:
            self.udpsocket.bind((self.addr,self.udpport))
        except socket.error as e:
            print "Can't bind to UDP socket 53: ", e

    def startservice(self):
        """Starts the background services associated with a node."""
        Tracker.startservice(self)
        # Start a thread for the UDP server
        UDP_server_thread = Thread(target=self.udp_server_loop)
        UDP_server_thread.start()
        
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

    def ismyname(self, name):
        return name == self.mydomain

    def ismysubdomain(self, name):
        return name == self.mydomain
        
    def aresponse(self, question):
        for gname in [NODE_LEADER, NODE_REPLICA]:
            for address in self.groups[gname].get_addresses():
                yield address

    def nsresponse(self, question):
        for address in self.groups[NODE_NAMESERVER].get_addresses():
            yield address
        
    def txtresponse(self, question):
        txtstr = ''
        for groupname,group in self.groups.iteritems():
            txtstr += node_names[groupname] + ' = '
            for address in group.get_addresses():
                txtstr += str(address) + ' '
        return txtstr
    
    def handle_query(self, data, addr):
        f = open("nameserverlog", 'a')
        query = dns.message.from_wire(data)
        response = dns.message.make_response(query)
        f.write(strftime("%Y-%m-%d %H:%M:%S")+'\n')
        for question in query.question:
            f.write("\nReceived Query for %s\n" % question.name)
            print "Question Name: ", question.name
            print "My Domain: ", self.mydomain
            if question.rdtype in [dns.rdatatype.A, dns.rdatatype.TXT] and self.ismyname(question.name):
                f.write("This is me %s" % str(question)) 
                flagstr = 'QR AA RD' # response, authoritative, recursion
                answerstr = ''    
                # A Queries --> List all Replicas starting with the Leader
                if question.rdtype == dns.rdatatype.A:
                    for address in self.aresponse(question):
                        answerstr += self.create_answer_section(question, addr=address)
                # TXT Queries --> List all nodes
                elif question.rdtype == dns.rdatatype.TXT:
                    answerstr += self.create_answer_section(question, txt=self.txtresponse(question))
                responsestr = self.create_response(response.id,opcode=dns.opcode.QUERY,rcode=dns.rcode.NOERROR,flags=flagstr,question=question.to_text(),answer=answerstr,authority='',additional='')
                print responsestr
                response = dns.message.from_text(responsestr)
            elif question.rdtype == dns.rdatatype.NS and self.ismyname(question.name):
                f.write("This is for my name server %s" % str(question)) 
                flagstr = 'QR AA RD' # response, authoritative, recursion
                answerstr = ''    
                for address in self.nsresponse(question):
                    print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", address
                    answerstr += self.create_answer_section(question, addr=address)
                responsestr = self.create_response(response.id,opcode=dns.opcode.QUERY,rcode=dns.rcode.NOERROR,flags=flagstr,question=question.to_text(),answer=answerstr,authority='',additional='')
                print responsestr
                response = dns.message.from_text(responsestr)
            else:
                f.write("Name Error\n")
                flags = QR + AA + RD + dns.rcode.NXDOMAIN
                response.flags = flags
        f.write( "\nRESPONSE:\n%s\n---\n" % response)
        self.udpsocket.sendto(response.to_wire(), addr)
        f.close()

    def create_response(self, id, opcode=0, rcode=0, flags='', question='', answer='', authority='', additional=''):
        responsestr = "id %s\nopcode %s\nrcode %s\nflags %s\n;QUESTION\n%s\n;ANSWER\n%s\n;AUTHORITY\n%s\n;ADDITIONAL\n%s\n" % (str(id), OPCODES[opcode], RCODES[rcode], flags, question, answer, authority, additional)
        return responsestr

    def create_answer_section(self, question, ttl='3600', rrclass=1, addr='', name='', txt=None):
        if question.rdtype == dns.rdatatype.A or dns.rdatatype.TXT:
            answerstr = "%s %s %s %s %s\n" % (str(question.name), str(ttl), str(RRCLASS[rrclass]), str(RRTYPE[question.rdtype]), str(addr) if txt is None else '"%s"' % txt)
        elif question.rdtype == dns.rdatatype.NS:
            answerstr = "%s %s %s %s %s\n" % (str(question.name), str(ttl), str(RRCLASS[rrclass]), str(RRTYPE[question.rdtype]), str(name))
        return answerstr
    
    def create_authority_section(self, question, ttl='3600', rrclass=1, rrtype=1, addr='', name=''):
        if rrtype == dns.rdatatype.A:
            authoritystr = "%s %s %s %s %s\n" % (str(question.name), str(ttl), str(RRCLASS[rrclass]), str(RRTYPE[rrtype]), str(addr))
        elif rrtype == dns.rdatatype.NS:
            authoritystr = "%s %s %s %s %s\n" % (str(question.name), str(ttl), str(RRCLASS[rrclass]), str(RRTYPE[rrtype]), str(name))
        return authoritystr

    def create_additional_section(self, question, ttl='3600', rrclass=1, rrtype=1, addr='', name=''):
        if rrtype == dns.rdatatype.A:
            additionalstr = "%s %s %s %s %s\n" % (str(question.name), str(ttl), str(RRCLASS[rrclass]), str(RRTYPE[rrtype]), str(addr))
        elif rrtype == dns.rdatatype.NS:
            additionalstr = "%s %s %s %s %s\n" % (str(question.name), str(ttl), str(RRCLASS[rrclass]), str(RRTYPE[rrtype]), str(name))
        return additionalstr

def main():
    nameservernode = Nameserver(options.dnsname)
    nameservernode.startservice()
    signal.signal(signal.SIGINT, nameservernode.interrupt_handler)
    signal.signal(signal.SIGTERM, nameservernode.terminate_handler)
    signal.pause()

if __name__=='__main__':
    main()

## RRTYPE
# A               1 a host address
# NS              2 an authoritative name server
# CNAME           5 the canonical name for an alias
# SOA             6 marks the start of a zone of authority
## CLASS
# IN              1 the Internet
