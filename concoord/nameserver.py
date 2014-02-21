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
from concoord.pack import *
from concoord.proxy.nameservercoord import NameserverCoord
import concoord.concoordroute53
import concoord.route53
try:
    import dns.exception
    import dns.message
    import dns.rcode
    import dns.opcode
    import dns.rdatatype
    import dns.name
    from dns.flags import *
except:
    print "To use the nameserver stand-alone, install dnspython: http://www.dnspython.org/"
try:
    from boto.route53.connection import Route53Connection
    import boto
except:
    print "To use Amazon Route 53, install boto: http://github.com/boto/boto/"

RRTYPE = ['','A','NS','MD','MF','CNAME','SOA', 'MB', 'MG', 'MR', 'NULL', 'WKS', 'PTR', 'HINFO', 'MINFO', 'MX', 'TXT', 'RP', 'AFSDB', 'X25', 'ISDN', 'RT', 'NSAP', 'NSAP_PTR', 'SIG', 'KEY', 'PX', 'GPOS', 'AAAA', 'LOC', 'NXT', '', '', 'SRV']
RRCLASS = ['','IN','CS','CH','HS']
OPCODES = ['QUERY','IQUERY','STATUS']
RCODES = ['NOERROR','FORMERR','SERVFAIL','NXDOMAIN','NOTIMP','REFUSED']

SRVNAME = '_concoord._tcp.'

class Nameserver(Replica):
    """Nameserver keeps track of the connectivity state of the system and replies to
    QUERY messages from dnsserver."""
    def __init__(self,
                 domain=args.domain,
                 master=args.master,
                 servicetype=args.type,
                 instantiateobj=False):
        Replica.__init__(self, nodetype=NODE_NAMESERVER, instantiateobj=instantiateobj, port=5000, bootstrap=args.bootstrap)
        if servicetype:
            self.servicetype = int(servicetype)
        else:
            if self.debug: self.logger.write("Initialization Error", "Service type of the nameserver is required. Use -t option.")
            self._graceexit(1)
        self.ipconverter = '.ipaddr.'+domain+'.'
        try:
            if domain.find('.') > 0:
                self.mydomain = dns.name.Name((domain+'.').split('.'))
            else:
                self.mydomain = domain
            self.mysrvdomain = dns.name.Name((SRVNAME+domain+'.').split('.'))
        except dns.name.EmptyLabel:
            self.logger.write("Initialization Error", "A DNS name is required. Use -n option.")
            self._graceexit(1)

        if self.servicetype == NS_SLAVE:
            if master:
                self.master = master
            else:
                self.logger.write("Initialization Error", "A master is required. Use -m option.")
                self._graceexit(1)
        elif self.servicetype == NS_ROUTE53:
            try:
                CONFIGDICT = load_configdict(args.configpath)
                AWS_ACCESS_KEY_ID = CONFIGDICT['AWS_ACCESS_KEY_ID']
                AWS_SECRET_ACCESS_KEY = CONFIGDICT['AWS_SECRET_ACCESS_KEY']
            except:
                print "To use Amazon Route 53, set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY in the configfile and use -o option for configpath."
                self._graceexit(1)
            # initialize Route 53 connection
            self.route53_name = domain+'.'
            self.route53_conn = Route53Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
            # get the zone_id for the domainname, the domainname
            # should be added to the zones beforehand
            self.route53_zone_id = concoord.concoordroute53.get_zone_id(self.route53_conn, self.route53_name)
            self.updateroute53()
        elif self.servicetype == NS_MASTER:
            self.udpport = 53
            self.udpsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            try:
                self.udpsocket.bind((self.addr,self.udpport))
            except socket.error as e:
                if self.debug: self.logger.write("DNS Error", "Can't bind to UDP port 53: %s" % str(e))
                self._graceexit(1)
        else:
            if self.debug: self.logger.write("Initialization Error", "Servicetype is required. Use -t option.")
            self._graceexit(1)

        # When the nameserver starts the revision number is 00 for that day
        self.revision = strftime("%Y%m%d", gmtime())+str(0).zfill(2)

    def startservice(self):
        """Starts the background services associated with a node."""
        Replica.startservice(self)
        if self.servicetype == NS_MASTER:
            # Start a thread for the UDP server
            UDP_server_thread = Thread(target=self.udp_server_loop, name='UDPServerThread')
            UDP_server_thread.start()

    def udp_server_loop(self):
        while self.alive:
            try:
                inputready,outputready,exceptready = select.select([self.udpsocket],[],[self.udpsocket])
                for s in exceptready:
                    if self.debug: self.logger.write("DNS Error", s)
                for s in inputready:
                    data,clientaddr = self.udpsocket.recvfrom(UDPMAXLEN)
                    if self.debug: self.logger.write("DNS State", "received a message from address %s" % str(clientaddr))
                    self.handle_query(data,clientaddr)
            except KeyboardInterrupt, EOFError:
                os._exit(0)
            except:
                continue
        self.udpsocket.close()
        return

    def aresponse(self, question=''):
        for address in get_addresses(self.replicas):
            yield address

    def nsresponse(self, question=''):
        for address in get_addresses(self.nameservers):
            yield address
        yield self.addr

    def srvresponse(self, question=''):
        for address,port in get_addressportpairs(self.replicas):
            yield address+self.ipconverter,port

    def txtresponse(self, question=''):
        txtstr = ''
        for groupname,group in self.groups.iteritems():
            for peer in group:
                txtstr += node_names[peer.type] +' '+ peer.addr + ':' + str(peer.port) + ';'
        txtstr += node_names[self.type] +' '+ self.addr + ':' + str(self.port)
        return txtstr

    def ismydomainname(self, question):
        return question.name == self.mydomain or (question.rdtype == dns.rdatatype.SRV and question.name == self.mysrvdomain)

    def should_answer(self, question):
        return (question.rdtype == dns.rdatatype.AAAA or \
                    question.rdtype == dns.rdatatype.A or \
                    question.rdtype == dns.rdatatype.TXT or \
                    question.rdtype == dns.rdatatype.NS or \
                    question.rdtype == dns.rdatatype.SRV or \
                    question.rdtype == dns.rdatatype.SOA) and self.ismydomainname(question)

    def handle_query(self, data, addr):
        query = dns.message.from_wire(data)
        response = dns.message.make_response(query)
        for question in query.question:
            if self.debug: self.logger.write("DNS State", "Received Query for %s\n" % question.name)
            if self.debug: self.logger.write("DNS State", "Mydomainname: %s Questionname: %s" % (self.mydomain, str(question.name)))
            if self.should_answer(question):
                if self.debug: self.logger.write("DNS State", "Query for my domain: %s" % str(question))
                flagstr = 'QR AA' # response, authoritative
                answerstr = ''
                if question.rdtype == dns.rdatatype.AAAA:
                    flagstr = 'QR' # response
                elif question.rdtype == dns.rdatatype.A:
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
                if self.debug: self.logger.write("DNS State", "UNSUPPORTED QUERY, %s" %str(question))
                return
        if self.debug: self.logger.write("DNS State", "RESPONSE:\n%s\n---\n" % str(response))
        try:
            self.udpsocket.sendto(response.to_wire(), addr)
        except:
            if self.debug: self.logger.write("DNS Error", "Cannot send RESPONSE:\n%s\n---\n" % str(response))

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

    def create_srv_answer_section(self, question, ttl=30, rrclass=1, priority=0, weight=100, port=None, addr=''):
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
        if self.debug: self.logger.write("State", "Adding node: %s %s" % (node_names[nodetype], nodename))
        ipaddr,port = nodename.split(":")
        nodepeer = Peer(ipaddr,int(port),nodetype)
        self.groups[nodetype][nodepeer] = 0
        self.updaterevision()
        if self.servicetype == NS_SLAVE:
            self.updatemaster(nodepeer, add=True)
        elif self.servicetype == NS_ROUTE53:
            self.updateroute53()

    def _del_node(self, nodetype, nodename):
        nodetype = int(nodetype)
        if self.debug: self.logger.write("State", "Deleting node: %s %s" % (node_names[nodetype], nodename))
        ipaddr,port = nodename.split(":")
        nodepeer = Peer(ipaddr,int(port),nodetype)
        del self.groups[nodetype][nodepeer]
        self.updaterevision()
        if self.servicetype == NS_SLAVE:
            self.updatemaster(nodepeer)
        elif self.servicetype == NS_ROUTE53:
            self.updateroute53()

    ########## ROUTE 53 ##########

    def route53_a(self):
        values = []
        for address in get_addresses(self.replicas):
            values.append(address)
        return ','.join(values)

    def route53_srv(self):
        values = []
        priority=0
        weight=100
        for address,port in get_addressportpairs(self.replicas):
            values.append('%d %d %d %s' % (priority, weight, port, address+self.ipconverter))
        return ','.join(values)

    def route53_txt(self):
        txtstr = self.txtresponse()
        lentxtstr = len(txtstr)
        strings = ["\""+txtstr[0:253]+"\""]
        if lentxtstr > 253:
            # cut the string in chunks
            for i in range(lentxtstr/253):
                strings.append("\""+txtstr[i*253:(i+1)*253]+"\"")
        return strings

    def updateroute53(self):
        if self.debug: self.logger.write("State", "Updating Route 53")
        # type A: update only if added node is a Replica
        rtype = 'A'
        newvalue = self.route53_a()
        # type SRV: update only if added node is a Replica
        rtype = 'SRV'
        newvalue = self.route53_srv()
        # type TXT: All Nodes
        rtype = 'TXT'
        newvalue = ','.join(self.route53_txt())

    ########## MASTER ##########
    def master_srv(self):
        values = []
        priority = 0
        weight = 100
        for address,port in get_addressportpairs(self.replicas):
            values.append('%d %d %d %s' % (priority, weight, port, address+self.ipconverter))
        return values

    def updatemaster(self, node, add=True):
        if self.debug: self.logger.write("State", "Updating Master at %s" % self.master)
        nscoord = NameserverCoord(self.master)
        nodes = {}
        for nodetype,group in self.groups.iteritems():
            nodes[nodetype] = set()
            for address,port in get_addressportpairs(self.groups[nodetype]):
                nodes[nodetype].add(address + ':' + str(port))
        nodes[self.type].add(self.addr + ':' + str(self.port))
        nscoord.updatesubdomain(str(self.mydomain), nodes)

    def updaterevision(self):
        if self.debug: self.logger.write("State", "Updating Revision -- from: %s" % self.revision)
        if strftime("%Y%m%d", gmtime()) in self.revision:
            rno = int(self.revision[-2]+self.revision[-1])
            rno += 1
            self.revision = strftime("%Y%m%d", gmtime())+str(rno).zfill(2)
        else:
            self.revision = strftime("%Y%m%d", gmtime())+str(0).zfill(2)
        if self.debug: self.logger.write("State", "Updating Revision -- to: %s" % self.revision)

def main():
    nameservernode = Nameserver(instantiateobj=True)
    nameservernode.startservice()
    signal.signal(signal.SIGINT, nameservernode.terminate_handler)
    signal.signal(signal.SIGTERM, nameservernode.terminate_handler)
    signal.pause()

if __name__=='__main__':
    main()
