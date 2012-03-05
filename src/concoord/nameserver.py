"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: The Nameserver keeps track of the view by being involved in Paxos rounds and replies to DNS queries with the latest view.
@copyright: See LICENSE
"""
import socket, select, signal
from time import strftime, gmtime
from threading import Thread, Timer
from concoord.node import *
from concoord.utils import *
from concoord.enums import *
from concoord.replica import *
from concoord.proxy.nameservercoord import NameserverCoord
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

SRVNAME = '_concoord._tcp.'

class Nameserver(Replica):
    """Nameserver keeps track of the connectivity state of the system and replies to
    QUERY messages from dnsserver."""
    def __init__(self, domain=options.dnsname, instantiateobj=False, master='128.84.227.201:14000'):
        Replica.__init__(self, nodetype=NODE_NAMESERVER, instantiateobj=instantiateobj, port=5000, bootstrap=options.bootstrap)
        try:
            self.mydomain = dns.name.Name((domain+'.').split('.'))
            self.mysrvdomain = dns.name.Name((SRVNAME+domain+'.').split('.'))
            self.ipconverter = '.ipaddr.'+domain+'.'
        except dns.name.EmptyLabel:
            self.logger.write("DNS Error", "A DNS name is required. Use -n option.")            
        self.udpport = 53
        self.udpsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        if master:
            self.master = master
        try:
            self.udpsocket.bind((self.addr,self.udpport))
        except socket.error as e:
            self.logger.write("DNS Error", "Can't bind to UDP port 53: %s" % str(e))
            #self._graceexit(1)
        # When the nameserver starts the revision number is 00 for that day
        self.revision = strftime("%Y%m%d", gmtime())+str(0).zfill(2)

    def startservice(self):
        """Starts the background services associated with a node."""
        Replica.startservice(self)
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
            yield address+self.ipconverter,port
        
    def txtresponse(self, question):
        txtstr = ''
        for groupname,group in self.groups.iteritems():
            for peer in group:
                txtstr += node_names[peer.type] +' '+ peer.addr + ':' + str(peer.port) + ';'
        txtstr += node_names[self.type] +' '+ self.addr + ':' + str(self.port)
        return txtstr

    def ismydomainname(self, question):
        return question.name == self.mydomain or (question.rdtype == dns.rdatatype.SRV and question.name == self.mysrvdomain)

    def should_answer(self, question):
        return (question.rdtype == dns.rdatatype.A or question.rdtype == dns.rdatatype.TXT or \
                question.rdtype == dns.rdatatype.NS or question.rdtype == dns.rdatatype.SRV or question.rdtype == dns.rdatatype.SOA) and self.ismydomainname(question)

    def handle_query(self, data, addr):
        query = dns.message.from_wire(data)
        response = dns.message.make_response(query)
        for question in query.question:
            self.logger.write("DNS State", "Received Query for %s\n" % question.name)
            self.logger.write("DNS State", "Mydomainname: %s Questionname: %s" % (self.mydomain, str(question.name)))
            if self.should_answer(question):
                self.logger.write("DNS State", "Query for my domain: %s" % str(question))
                flagstr = 'QR AA' # response, authoritative
                answerstr = ''
                if question.rdtype == dns.rdatatype.A:
                    # A Queries --> List all Replicas starting with the Leader
                    for address in self.aresponse(question):
                        answerstr += self.create_answer_section(question, addr=address)
                elif question.rdtype == dns.rdatatype.TXT:
                    # TXT Queries --> List all nodes
                    answerstr = self.create_answer_section(question, txt=self.txtresponse(question))
                elif question.rdtype == dns.rdatatype.NS:
                    # NS Queries --> List all Nameserver nodes
                    for address in self.nsresponse(question):
                        answerstr += self.create_answer_section(question, name=address)
                elif question.rdtype == dns.rdatatype.SOA:
                    # SOA Query --> Reply with Metadata
                    answerstr = self.create_soa_answer_section(question)
                elif question.rdtype == dns.rdatatype.SRV:
                    # SRV Queries --> List all Replicas with addr:port
                    for address,port in self.srvresponse(question):
                        answerstr += self.create_srv_answer_section(question, addr=address, port=port)
                responsestr = self.create_response(response.id,opcode=dns.opcode.QUERY,
                                                   rcode=dns.rcode.NOERROR,flags=flagstr,
                                                   question=question.to_text(),answer=answerstr,
                                                   authority='',additional='')
                response = dns.message.from_text(responsestr)
            else:
                self.logger.write("DNS State", "Name Error, %s" %str(question))
                response.flags = QR + AA + dns.rcode.NXDOMAIN
        self.logger.write("DNS State", "RESPONSE:\n%s\n---\n" % str(response))
        try:
            self.udpsocket.sendto(response.to_wire(), addr)
        except:
            self.logger.write("DNS Error", "Cannot send RESPONSE:\n%s\n---\n" % str(response))

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

    def create_mx_answer_section(self, question, ttl=30, rrclass=1, priority=0, addr=''):
        answerstr = "%s %d %s %s %d %s\n" % (str(question.name), ttl, RRCLASS[rrclass], RRTYPE[question.rdtype], priority, addr)
        return answerstr

    def create_soa_answer_section(self, question, ttl=30, rrclass=1):
        refreshrate = 86000 # time (in seconds) when the slave DNS server will refresh from the master
        updateretry = 7200  # time (in seconds) when the slave DNS server should retry contacting a failed master
        expiry = 360000     # time (in seconds) that a slave server will keep a cached zone file as valid
        minimum = 432000    # default time (in seconds) that the slave servers should cache the Zone file
        answerstr = "%s %d %s %s %s %s (%s %d %d %d %d)" % (str(question.name), ttl, RRCLASS[rrclass],
                                                            RRTYPE[question.rdtype],
                                                            str(self.mydomain),
                                                            'dns-admin.'+str(self.mydomain),
                                                            self.revision,
                                                            refreshrate,
                                                            updateretry,
                                                            expiry,
                                                            minimum)
        return answerstr

    def create_answer_section(self, question, ttl=30, rrclass=1, addr='', name='', txt=None):
        if question.rdtype == dns.rdatatype.A:
            resp = str(addr)
        elif question.rdtype == dns.rdatatype.TXT:
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

    def _add_node(self, nodetype, nodename):
        nodetype = int(nodetype)
        self.logger.write("State", "Adding node: %s %s" % (node_names[nodetype], nodename))
        ipaddr,port = nodename.split(":")
        nodepeer = Peer(ipaddr,int(port),nodetype)
        self.groups[nodetype].add(nodepeer)
        self.updaterevision()
        self.updatemaster(nodepeer, add=True)
        
    def _del_node(self, nodetype, nodename):
        nodetype = int(nodetype)
        self.logger.write("State", "Deleting node: %s %s" % (node_names[nodetype], nodename))
        ipaddr,port = nodename.split(":")
        nodepeer = Peer(ipaddr,int(port),nodetype)
        self.groups[nodetype].remove(nodepeer)
        self.updaterevision()
        self.updatemaster(nodepeer)

    def updatemaster(self, node, add=True, route53=False):
        self.logger.write("State", "**************************************Updating Master")
        # Master can be a Nameserver that uses a Coordination Object
        # or Amazon Route 53
        if route53:
            pass
        else:
            # XXX The representation of a node in the Coordination
            # Object may need change
            print self.master
            print str(self.mydomain)
            print type(str(self.mydomain))
            nscoord = NameserverCoord(self.master)
            if add:
                print str(self.mydomain), str(node.addr)
                nscoord.addnodetosubdomain(str(self.mydomain), str(node.addr))
            else:
                nscoord.delnodefromsubdomain(str(self.mydomain), str(node.addr))

    def updaterevision(self):
        self.logger.write("State", "Updating Revision -- from: %s" % self.revision)
        if strftime("%Y%m%d", gmtime()) in self.revision:
            rno = int(self.revision[-2]+self.revision[-1])
            rno += 1
            self.revision = strftime("%Y%m%d", gmtime())+str(rno).zfill(2)
        else:
            self.revision = strftime("%Y%m%d", gmtime())+str(0).zfill(2)
        self.logger.write("State", "Updating Revision -- to: %s" % self.revision)

def main():
    nameservernode = Nameserver(options.dnsname, instantiateobj=True)
    nameservernode.startservice()
    signal.signal(signal.SIGINT, nameservernode.terminate_handler)
    signal.signal(signal.SIGTERM, nameservernode.terminate_handler)
    signal.pause()

if __name__=='__main__':
    main()
