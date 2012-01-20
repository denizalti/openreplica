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
    print "Install dnspython: http://www.dnspython.org/"

RRTYPE = ['','A','NS','MD','MF','CNAME','SOA', 'MB', 'MG', 'MR', 'NULL', 'WKS', 'PTR', 'HINFO', 'MINFO', 'MX', 'TXT', 'RP', 'AFSDB', 'X25', 'ISDN', 'RT', 'NSAP', 'NSAP_PTR', 'SIG', 'KEY', 'PX', 'GPOS', 'AAAA', 'LOC', 'NXT', '', '', 'SRV']
RRCLASS = ['','IN','CS','CH','HS']
OPCODES = ['QUERY','IQUERY','STATUS']
RCODES = ['NOERROR','FORMERR','SERVFAIL','NXDOMAIN','NOTIMP','REFUSED']

IPCONVERTER = '.ipaddr.openreplica.org.'
SRVNAME = '_concoord._tcp.hack.'

class Nameserver(Tracker):
    """Nameserver keeps track of the connectivity state of the system and replies to
    QUERY messages from dnsserver."""
    def __init__(self, domain, instantiateobj=False):
        Tracker.__init__(self, nodetype=NODE_NAMESERVER, instantiateobj=instantiateobj, port=5000, bootstrap=options.bootstrap)
        self.mydomain = dns.name.Name((domain+".").split("."))
        self.mysrvdomain = dns.name.Name((SRVNAME+domain+".").split("."))
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
        UDP_server_thread = Thread(target=self.udp_server_loop, name='UDPServerThread')
        UDP_server_thread.start()
        
    def udp_server_loop(self):
        while self.alive:
            try:
                inputready,outputready,exceptready = select.select([self.udpsocket],[],[self.udpsocket])
                for s in exceptready:
                    self.logger.write("DNS Error", s)
                for s in inputready:
                    data,clientaddr = self.udpsocket.recvfrom(UDPMAXLEN)
                    self.logger.write("DNS State", "received a message from address %s" % str(clientaddr))
                    self.handle_query(data,clientaddr)
            except KeyboardInterrupt, EOFError:
                os._exit(0)
        self.udpsocket.close()
        return

    def ismysubdomain(self, name):
        return name == self.mydomain
        
    def aresponse(self, question):
        addresses = self.groups[NODE_REPLICA].get_addresses()
        for address,port in addresses:
            yield address

    def nsresponse(self, question):
        for address,port in self.groups[NODE_NAMESERVER].get_addresses():
            yield address
        yield self.addr

    def srvresponse(self, question):
        for address,port in self.groups[NODE_REPLICA].get_addresses():
            yield address+IPCONVERTER,port
        
    def txtresponse(self, question):
        txtstr = ''
        for groupname,group in self.groups.iteritems():
            if len(group) > 0 or node_names[groupname] == 'NAMESERVER':
                txtstr += ";" + node_names[groupname]
            peers = []
            for peer in group:
                txtstr += ','
                peers.append(peer.addr + ':' + str(peer.port))
            txtstr += ','.join(peers) 
        txtstr += ',' + self.addr + ':' + str(self.port)
        return txtstr[1:]

    def handle_query(self, data, addr):
        query = dns.message.from_wire(data)
        response = dns.message.make_response(query)
        for question in query.question:
            self.logger.write("DNS State", "Received Query for %s\n" % question.name)
            if (question.rdtype == dns.rdatatype.A or question.rdtype == dns.rdatatype.AAAA) and question.name == self.mydomain:
                # This is an A Query for my name, I should handle it
                self.logger.write("DNS State", ">>>>>>>>>>>>>> A Query for my domain: %s" % str(question))
                flagstr = 'QR AA' # response, authoritative, recursion
                answerstr = ''    
                # A Queries --> List all Replicas starting with the Leader
                for address in self.aresponse(question):
                    answerstr += self.create_answer_section(question, addr=address)
                responsestr = self.create_response(response.id,opcode=dns.opcode.QUERY,rcode=dns.rcode.NOERROR,flags=flagstr,question=question.to_text(),answer=answerstr,authority='',additional='')
                response = dns.message.from_text(responsestr)

            elif question.rdtype == dns.rdatatype.TXT and question.name == self.mydomain:
                # This is an TXT Query for my name, I should handle it
                self.logger.write("DNS State", ">>>>>>>>>>>>>> TXT Query for my domain: %s" % str(question))
                flagstr = 'QR AA' # response, authoritative, recursion
                answerstr = ''
                # TXT Queries --> List all nodes
                answerstr = self.create_answer_section(question, txt=self.txtresponse(question))
                responsestr = self.create_response(response.id,opcode=dns.opcode.QUERY,rcode=dns.rcode.NOERROR,flags=flagstr,question=question.to_text(),answer=answerstr,authority='',additional='')
                response = dns.message.from_text(responsestr)

            elif question.rdtype == dns.rdatatype.NS and question.name == self.mydomain:
                # This is an NS Query for my name, I should handle it
                self.logger.write("DNS State", ">>>>>>>>>>>>>> NS Query for my domain: %s" % str(question)) 
                flagstr = 'QR AA' # response, authoritative, recursion
                answerstr = ''
                # NS Queries --> List all Nameserver nodes
                for address in self.nsresponse(question):
                    answerstr += self.create_answer_section(question, addr=address)
                responsestr = self.create_response(response.id,opcode=dns.opcode.QUERY,rcode=dns.rcode.NOERROR,flags=flagstr,question=question.to_text(),answer=answerstr,authority='',additional='')
                response = dns.message.from_text(responsestr)

            elif question.rdtype == dns.rdatatype.SRV and question.name == self.mydomain:
                # This is an SRV Query for my name, I should handle it
                self.logger.write("DNS State", ">>>>>>>>>>>>>> SRV Query for my domain: %s" % str(question)) 
                flagstr = 'QR AA' # response, authoritative
                answerstr = ''
                # SRV Queries --> List all Replicas with addr:port
                for address,port in self.srvresponse(question):
                    answerstr += self.create_srv_answer_section(question, addr=address, port=port)
                responsestr = self.create_response(response.id,opcode=dns.opcode.QUERY,rcode=dns.rcode.NOERROR,flags=flagstr,question=question.to_text(),answer=answerstr,authority='',additional='')
                response = dns.message.from_text(responsestr)

            else:
                # This Query is not something I know how to respond to
                self.logger.write("DNS State", ">>>>>>>>>>>>>> Name Error, %s" %str(question))
                flags = QR + AA + dns.rcode.NXDOMAIN
                response.flags = flags
        self.logger.write("DNS State", ">>>>>>>>>>>>>> RESPONSE:\n%s\n---\n" % str(response))
        try:
            self.udpsocket.sendto(response.to_wire(), addr)
        except:
            print ">>>>>>>>>>>>>>>>>>>>>>>>>>>> Cannot respond to query."

    def create_response(self, id, opcode=0, rcode=0, flags='', question='', answer='', authority='', additional=''):
        answerstr     = ';ANSWER\n'     + answer     + '\n' if answer != '' else ''
        authoritystr  = ';AUTHORITY\n'  + authority  + '\n' if authority != '' else ''
        additionalstr = ';ADDITIONAL\n' + additional + '\n' if additional != '' else ''

        responsestr = "id %s\nopcode %s\nrcode %s\nflags %s\n;QUESTION\n%s\n%s%s%s" % (str(id), 
                                                                                       OPCODES[opcode], 
                                                                                       RCODES[rcode], 
                                                                                       flags, 
                                                                                       question, 
                                                                                       answerstr, authoritystr, additionalstr)
        return responsestr

    def create_srv_answer_section(self, question, ttl=30, rrclass=1, priority=0, weight=100, port='', addr=''):
        answerstr = "%s %d %s %s %d %d %d %s\n" % (str(question.name), ttl, RRCLASS[rrclass], RRTYPE[question.rdtype], priority, weight, port, addr)
        return answerstr

    def create_answer_section(self, question, ttl=30, rrclass=1, addr='', name='', txt=None):
        if question.rdtype == dns.rdatatype.A:
            resp = str(addr)
        elif dns.rdatatype.TXT:
            resp = '"%s"' % txt
        elif question.rdtype == dns.rdatatype.NS:
            resp = str(name)
        answerstr = "%s %s %s %s %s\n" % (str(question.name), str(ttl), str(RRCLASS[rrclass]), str(RRTYPE[question.rdtype]), resp)
        return answerstr
    
    def create_authority_section(self, question, ttl='30', rrclass=1, rrtype=1, nshost=''):
        authoritystr = "%s %s %s %s %s\n" % (str(question.name), str(ttl), str(RRCLASS[rrclass]), str(RRTYPE[rrtype]), str(nshost))
        return authoritystr

    def create_additional_section(self, question, ttl='30', rrclass=1, rrtype=1, addr=''):
        additionalstr = "%s %s %s %s %s\n" % (str(question.name), str(ttl), str(RRCLASS[rrclass]), str(RRTYPE[rrtype]), str(addr))
        return additionalstr

def main():
    nameservernode = Nameserver(options.dnsname, instantiateobj=True)
    nameservernode.startservice()
    signal.signal(signal.SIGINT, nameservernode.terminate_handler)
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
