from nameserver import *

#OPENREPLICANS = {'ns1.openreplica.org.':'128.84.60.206', 'ns2.openreplica.org.':'128.84.60.206'}
OPENREPLICANS = {'ns1.openreplica.org.':'128.84.154.110', 'ns2.openreplica.org.':'128.84.154.110'} 

class OpenReplicaNameserver(Nameserver):
    def __init__(self):
        Nameserver.__init__(self, domain='openreplica.org', instantiateobj=True)
        self.specialdomain = dns.name.Name(['ipaddr','openreplica','org',''])
        self.nsdomains = []
        for nsdomain in OPENREPLICANS.iterkeys():
            self.nsdomains.append(dns.name.Name(nsdomain.split(".")))

    def performcore(self, msg, slotno, dometaonly=False, designated=False):
        Replica.performcore(self, msg, slotno, dometaonly, designated)

    def perform(self, msg):
        Replica.perform(self, msg)
            
    def msg_perform(self, conn, msg):
        Replica.msg_perform(self, conn, msg)

    def ismysubdomainname(self, name):
        for subdomain in self.object.nodes.keys():
            if name == dns.name.Name([subdomain, 'openreplica', 'org', '']):
                return True
        return False

    def ismysrvname(self, name):
        for subdomain in self.object.nodes.keys():
            if name == dns.name.Name(['_concoord', '_tcp', subdomain, 'openreplica', 'org', '']):
                return True
        return False

    def ismynsname(self, name):
        for nsdomain in OPENREPLICANS.iterkeys():
            if name == dns.name.Name(nsdomain.split(".")):
                return True
        return False
    
    def aresponse_ipaddr(self, question):
        # Asking for IPADDR.ipaddr.openreplica.org
        # Respond with IPADDR
        yield question.name.split(4)[0].to_text()

    def aresponse_ns(self, question):
        # Asking for ns1/ns2.openreplica.org
        # Respond with corresponding addr
        for nsdomain,nsaddr in OPENREPLICANS.iteritems():
            if dns.name.Name(nsdomain.split(".")) == question.name:
                yield nsaddr

    def nsresponse(self, question):
        if question.name == self.mydomain or question.name.is_subdomain(self.specialdomain):
            for address,port in self.groups[NODE_NAMESERVER].get_addresses():
                yield address+IPCONVERTER
            yield self.addr+IPCONVERTER
        for nsdomain,nsaddr in OPENREPLICANS.iteritems():
            yield nsdomain

    def nsresponse_subdomain(self, question):
        for subdomain in self.object.nodes.keys():
            if question.name == dns.name.Name([subdomain, 'openreplica', 'org', '']):
                for node in self.object.nodes[subdomain]:
                    addr,port = node.split(":")
                    yield addr+IPCONVERTER

    def srvresponse(self, question):
        for subdomain in self.object.nodes.keys():
            if question.name == dns.name.Name(['_concoord', '_tcp', subdomain, 'openreplica', 'org', '']):
                for node in self.object.nodes[subdomain]:
                    addr,port = node.split(":")
                    yield addr+IPCONVERTER,int(port)

    def handle_query(self, data, addr):
        query = dns.message.from_wire(data)
        response = dns.message.make_response(query)
        for question in query.question:
            self.logger.write("DNS State", "Received Query for %s\n" % question.name)
            if question.rdtype == dns.rdatatype.A:
                if question.name == self.mydomain:
                    # This is an A Query for my domain, I should handle it
                    self.logger.write("DNS State", ">>>>>>>>>>>>>> A Query for my domain: %s" % str(question))
                    flagstr = 'QR AA' # response, authoritative
                    answerstr = ''    
                    # A Queries --> List all Replicas starting with the Leader
                    for address in self.aresponse(question):
                        answerstr += self.create_answer_section(question, addr=address)
                    responsestr = self.create_response(response.id,opcode=dns.opcode.QUERY,rcode=dns.rcode.NOERROR,flags=flagstr,question=question.to_text(),answer=answerstr,authority='',additional='')
                    response = dns.message.from_text(responsestr)
                elif self.ismynsname(question.name):
                    # This is an A Query for my nameserver, I should handle it
                    self.logger.write("DNS State", ">>>>>>>>>>>>>> A Query for my nameserver: %s" % str(question))
                    flagstr = 'QR AA' # response, authoritative
                    answerstr = ''    
                    # A Queries --> List all Replicas starting with the Leader
                    for address in self.aresponse_ns(question):
                        answerstr += self.create_answer_section(question, addr=address)
                    responsestr = self.create_response(response.id,opcode=dns.opcode.QUERY,rcode=dns.rcode.NOERROR,flags=flagstr,question=question.to_text(),answer=answerstr,authority='',additional='')
                    response = dns.message.from_text(responsestr)
                elif question.name.is_subdomain(self.specialdomain):
                    # This is an A Query for the special ipaddr subdomain, I should handle it
                    self.logger.write("DNS State", ">>>>>>>>>>>>>> A Query for my specialsubdomain: %s" % str(question))
                    flagstr = 'QR AA' # response, authoritative
                    answerstr = ''    
                    # A Queries --> List all Replicas starting with the Leader
                    for address in self.aresponse_ipaddr(question):
                        answerstr += self.create_answer_section(question, addr=address)
                    responsestr = self.create_response(response.id,opcode=dns.opcode.QUERY,rcode=dns.rcode.NOERROR,flags=flagstr,question=question.to_text(),answer=answerstr,authority='',additional='')
                    response = dns.message.from_text(responsestr)
                # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
                elif self.ismysubdomainname(question.name):
                    # This is an A Query for my subdomain, I will reply with an NS response
                    self.logger.write("DNS State", ">>>>>>>>>>>>>> A Query for my subdomain: %s" % str(question))
                    flagstr = 'QR' # response, not authoritative
                    authstr = ''    
                    for address in self.nsresponse_subdomain(question):
                        print ">>>", address
                        authstr += self.create_authority_section(question, addr=address, rrtype=dns.rdatatype.NS)
                    addstr = ''    
                    for address in self.nsresponse_subdomain(question):
                        addstr += self.create_additional_section(question, addr=address)
                    responsestr = self.create_response(response.id,opcode=dns.opcode.QUERY,rcode=dns.rcode.NOERROR,flags=flagstr,question=question.to_text(),answer='',authority=authstr,additional=addstr)
                    print str(responsestr)
                    response = dns.message.from_text(responsestr)
            elif question.rdtype == dns.rdatatype.TXT and question.name == self.mydomain:
                # This is an TXT Query for my domain, I should handle it
                self.logger.write("DNS State", ">>>>>>>>>>>>>> TXT Query for my domain: %s" % str(question))
                flagstr = 'QR AA' # response, authoritative
                answerstr = ''
                # TXT Queries --> List all nodes
                answerstr = self.create_answer_section(question, txt=self.txtresponse(question))
                responsestr = self.create_response(response.id,opcode=dns.opcode.QUERY,rcode=dns.rcode.NOERROR,flags=flagstr,question=question.to_text(),answer=answerstr,authority='',additional='')
                response = dns.message.from_text(responsestr)
            elif question.rdtype == dns.rdatatype.NS:
                if question.name == self.mydomain:
                    # This is an NS Query for my domain, I should handle it
                    self.logger.write("DNS State", ">>>>>>>>>>>>>> NS Query for my domain: %s" % str(question)) 
                    flagstr = 'QR AA' # response, authoritative
                    answerstr = ''
                    # NS Queries --> List all Nameserver nodes
                    for address in self.nsresponse(question):
                        answerstr += self.create_answer_section(question, addr=address)
                    responsestr = self.create_response(response.id,opcode=dns.opcode.QUERY,rcode=dns.rcode.NOERROR,flags=flagstr,question=question.to_text(),answer=answerstr,authority='',additional='')
                    response = dns.message.from_text(responsestr)
                elif self.ismysubdomainname(question.name):
                    # This is an NS Query for my subdomain, I should handle it
                    self.logger.write("DNS State", ">>>>>>>>>>>>>> NS Query for my subdomain: %s" % str(question)) 
                    flagstr = 'QR AA' # response, authoritative
                    answerstr = ''
                    # NS Queries --> List Nameservers of my subdomain
                    for address in self.nsresponse_subdomain(question):
                        answerstr += self.create_answer_section(question, addr=address)
                    responsestr = self.create_response(response.id,opcode=dns.opcode.QUERY,rcode=dns.rcode.NOERROR,flags=flagstr,question=question.to_text(),answer=answerstr,authority='',additional='')
                    response = dns.message.from_text(responsestr)
            elif question.rdtype == dns.rdatatype.SRV and self.ismysrvname(question.name):
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

def main():
    nameservernode = OpenReplicaNameserver()
    nameservernode.startservice()
    signal.signal(signal.SIGINT, nameservernode.terminate_handler)
    signal.signal(signal.SIGTERM, nameservernode.terminate_handler)
    signal.pause()

if __name__=='__main__':
    main()
