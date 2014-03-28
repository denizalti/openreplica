'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: OpenReplicaNameserver that uses OpenReplica Coordination Object to keep track of nameservers of subdomains of OpenReplica.
@copyright: See LICENSE
'''
from time import strftime, gmtime
from concoord.nameserver import *

OPENREPLICANS = {'ns1.openreplica.org.':'128.84.154.110', 'ns2.openreplica.org.':'128.84.154.40'}
OPENREPLICAWEBHOST = '128.84.154.110'
VIEWCHANGEFUNCTIONS = ['addnodetosubdomain','delnodefromsubdomain','delsubdomain']

class OpenReplicaNameserver(Nameserver):
    def __init__(self):
        Nameserver.__init__(self, domain='openreplica.org', instantiateobj=True)
        self.mysrvdomain = dns.name.Name(['_concoord', '_tcp', 'openreplica', 'org', ''])
        self.specialdomain = dns.name.Name(['ipaddr','openreplica','org',''])
        self.nsdomains = []
        for nsdomain in OPENREPLICANS.iterkeys():
            self.nsdomains.append(dns.name.Name(nsdomain.split(".")))
        # When the nameserver starts the revision number is 00 for that day
        self.revision = strftime("%Y%m%d", gmtime())+str(0).zfill(2)

    def performcore(self, command, dometaonly=False, designated=False):
        Replica.performcore(self, command, dometaonly, designated)
        commandtuple = command.command
        if type(commandtuple) == str:
            commandname = commandtuple
        else:
            commandname = commandtuple[0]
        if commandname in VIEWCHANGEFUNCTIONS:
            self.updaterevision()

    def perform(self, msg):
        Replica.perform(self, msg)

    def msg_perform(self, conn, msg):
        Replica.msg_perform(self, conn, msg)

    def ismysubdomainname(self, question):
        for subdomain in self.object.getsubdomains():
            if question.name in [dns.name.Name([subdomain, 'openreplica', 'org', '']), dns.name.Name(['_concoord', '_tcp', subdomain, 'openreplica', 'org', ''])]:
                return True
        return False

    def ismynsname(self, question):
        for nsdomain in OPENREPLICANS.iterkeys():
            if question.name == dns.name.Name(nsdomain.split(".")):
                return True
        return False

    def aresponse(self, question=''):
        yield OPENREPLICAWEBHOST

    def aresponse_ipaddr(self, question):
        # Asking for IPADDR.ipaddr.openreplica.org
        # Respond with IPADDR
        yield question.name.split(4)[0].to_text()

    def aresponse_ns(self, question):
        # Asking for ns1/ns2/ns3.openreplica.org
        # Respond with corresponding addr
        for nsdomain,nsaddr in OPENREPLICANS.iteritems():
            if dns.name.Name(nsdomain.split(".")) == question.name:
                yield nsaddr

    def aresponse_subdomain(self, question):
        for subdomain in self.object.getsubdomains():
            subdomain = subdomain.strip('.')
            if question.name in [dns.name.Name([subdomain, 'openreplica', 'org', '']), dns.name.Name(['_concoord', '_tcp', subdomain, 'openreplica', 'org', ''])]:
                for node in self.object.getnodes(subdomain)[NODE_REPLICA]:
                    addr,port = node.split(":")
                    yield addr

    def nsresponse(self, question):
        if question.name == self.mydomain or question.name.is_subdomain(self.specialdomain) or self.ismysubdomainname(question):
            for address,port in get_addressportpairs(self.nameservers):
                yield address+self.ipconverter
            yield self.addr+self.ipconverter
        for nsdomain,nsaddr in OPENREPLICANS.iteritems():
            yield nsdomain

    def nsresponse_subdomain(self, question):
        for subdomain in self.object.getsubdomains():
            subdomain = subdomain.strip('.')
            if question.name in [dns.name.Name([subdomain, 'openreplica', 'org', '']), dns.name.Name(['_concoord', '_tcp', subdomain, 'openreplica', 'org', ''])]:
                for node in self.object.getnodes(subdomain)[NODE_NAMESERVER]:
                    addr,port = node.split(":")
                    yield addr+self.ipconverter

    def txtresponse_subdomain(self, question):
        txtstr = ''
        for subdomain in self.object.getsubdomains():
            subdomain = subdomain.strip('.')
            if question.name in [dns.name.Name([subdomain, 'openreplica', 'org', '']), dns.name.Name(['_concoord', '_tcp', subdomain, 'openreplica', 'org', ''])]:
                for nodetype,nodes in self.object.getnodes(subdomain).iteritems():
                    for node in nodes:
                        txtstr += node_names[nodetype] + ' ' + node + ';'
        return txtstr

    def srvresponse_subdomain(self, question):
        for subdomain in self.object.getsubdomains():
            subdomain = subdomain.strip('.')
            if question.name in [dns.name.Name([subdomain, 'openreplica', 'org', '']), dns.name.Name(['_concoord', '_tcp', subdomain, 'openreplica', 'org', ''])]:
                for node in self.object.getnodes(subdomain)[NODE_REPLICA]:
                    try:
                        addr,port = node.split(":")
                        yield addr+self.ipconverter,int(port)
                    except:
                        pass

    def should_answer(self, question):
        formyname = (question.rdtype == dns.rdatatype.A or question.rdtype == dns.rdatatype.TXT or question.rdtype == dns.rdatatype.NS or question.rdtype == dns.rdatatype.SRV or question.rdtype == dns.rdatatype.MX or question.rdtype == dns.rdatatype.SOA) and self.ismydomainname(question)
        formysubdomainname = (question.rdtype == dns.rdatatype.A or question.rdtype == dns.rdatatype.TXT or question.rdtype == dns.rdatatype.NS or question.rdtype == dns.rdatatype.SRV or question.rdtype == dns.rdatatype.SOA) and self.ismysubdomainname(question)
        myresponsibility_a = question.rdtype == dns.rdatatype.A and (self.ismynsname(question) or question.name.is_subdomain(self.specialdomain))
        myresponsibility_ns = question.rdtype == dns.rdatatype.NS and self.ismysubdomainname(question)
        return formyname or formysubdomainname or myresponsibility_a or myresponsibility_ns

    def should_auth(self, question):
        return (question.rdtype == dns.rdatatype.AAAA or question.rdtype == dns.rdatatype.A or question.rdtype == dns.rdatatype.TXT or question.rdtype == dns.rdatatype.SRV) and self.ismysubdomainname(question) or (question.rdtype == dns.rdatatype.AAAA and (self.ismydomainname(question) or self.ismysubdomainname(question) or question.name.is_subdomain(self.specialdomain)))

    def handle_query(self, data, addr):
        query = dns.message.from_wire(data)
        response = dns.message.make_response(query)
        for question in query.question:
            if self.debug: self.logger.write("DNS State", "Received Query for %s\n" % question.name)
            if self.debug: self.logger.write("DNS State", "Received Query %s\n" % question)
            if self.should_answer(question):
                flagstr = 'QR AA' # response, authoritative
                answerstr = ''
                if question.rdtype == dns.rdatatype.A:
                    if self.ismydomainname(question):
                        # A Queries --> List all Replicas starting with the Leader
                        for address in self.aresponse(question):
                            answerstr += self.create_answer_section(question, addr=address)
                    elif self.ismysubdomainname(question):
                        for address in self.aresponse_subdomain(question):
                            answerstr += self.create_answer_section(question, addr=address)
                    elif self.ismynsname(question):
                        # A Queries --> List all Replicas starting with the Leader
                        for address in self.aresponse_ns(question):
                            answerstr += self.create_answer_section(question, addr=address)
                    elif question.name.is_subdomain(self.specialdomain):
                        # A Query for ipaddr --> Respond with ipaddr
                        for address in self.aresponse_ipaddr(question):
                            answerstr += self.create_answer_section(question, addr=address)
                elif question.rdtype == dns.rdatatype.TXT:
                    if self.ismydomainname(question):
                        # TXT Queries --> List all nodes
                        answerstr = self.create_answer_section(question, txt=self.txtresponse(question))
                    elif self.ismysubdomainname(question):
                        answerstr = self.create_answer_section(question, txt=self.txtresponse_subdomain(question))
                elif question.rdtype == dns.rdatatype.NS:
                    if self.ismydomainname(question):
                        # NS Queries --> List all Nameserver nodes
                        for address in self.nsresponse(question):
                            answerstr += self.create_answer_section(question, name=address)
                    elif self.ismysubdomainname(question):
                        # NS Queries --> List Nameservers of my subdomain
                        #for address in self.nsresponse_subdomain(question):
                        for address in self.nsresponse(question):
                            answerstr += self.create_answer_section(question, name=address)
                elif question.rdtype == dns.rdatatype.SRV:
                    if self.ismydomainname(question):
                        # SRV Queries --> List all Replicas with addr:port
                        for address,port in self.srvresponse(question):
                            answerstr += self.create_srv_answer_section(question, addr=address, port=port)
                    elif self.ismysubdomainname(question):
                        for address,port in self.srvresponse_subdomain(question):
                            answerstr += self.create_srv_answer_section(question, addr=address, port=port)
                elif question.rdtype == dns.rdatatype.MX:
                    if self.ismydomainname(question):
                        # MX Queries --> mail.systems.cs.cornell.edu
                        answerstr = self.create_mx_answer_section(question, ttl=86400, addr='mail.systems.cs.cornell.edu.')
                elif question.rdtype == dns.rdatatype.SOA:
                    if self.ismydomainname(question) or self.ismysubdomainname(question):
                        # SOA Query --> Reply with Metadata
                        answerstr = self.create_soa_answer_section(question)
                responsestr = self.create_response(response.id,opcode=dns.opcode.QUERY,rcode=dns.rcode.NOERROR,flags=flagstr,question=question.to_text(),answer=answerstr,authority='',additional='')
                response = dns.message.from_text(responsestr)
            elif self.should_auth(question):
                if self.debug: self.logger.write("DNS State", "Query for my subdomain: %s" % str(question))
                flagstr = 'QR' # response, not authoritative
                authstr = ''
                for address in self.nsresponse_subdomain(question):
                    authstr += self.create_authority_section(question, nshost=address, rrtype=dns.rdatatype.NS)
                responsestr = self.create_response(response.id,opcode=dns.opcode.QUERY,rcode=dns.rcode.NOERROR,flags=flagstr,question=question.to_text(),answer='',authority=authstr,additional='')
                response = dns.message.from_text(responsestr)
            else:
                # This Query is not something I know how to respond to
                if self.debug: self.logger.write("DNS State", "UNSUPPORTED QUERY, %s" %str(question))
                return
        if self.debug: self.logger.write("DNS State", "RESPONSE:\n%s\n---\n" % str(response))
        try:
            self.udpsocket.sendto(response.to_wire(), addr)
        except:
            if self.debug: self.logger.write("DNS Error", "Cannot send RESPONSE:\n%s\n---\n" % str(response))

def main():
    nameservernode = OpenReplicaNameserver()
    nameservernode.startservice()
    signal.signal(signal.SIGINT, nameservernode.terminate_handler)
    signal.signal(signal.SIGTERM, nameservernode.terminate_handler)
    signal.pause()

if __name__=='__main__':
    main()
