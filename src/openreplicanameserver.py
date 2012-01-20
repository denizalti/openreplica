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

    def ismyname(self, name):
        return name == self.mydomain or name.is_subdomain(self.specialdomain) or self.ismysubdomainname(name) or self.ismynsname(name) or self.ismysrvname(name)

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

    def aresponse(self, question):
        if question.name.is_subdomain(self.specialdomain):
            # Asking for XXX.ipaddr.openreplica.org
            # Respond with XXX
            yield question.name.split(4)[0].to_text()
        elif self.ismynsname(question.name):
            # Asking for ns1/ns2.openreplica.org
            # Respond with corresponding addr
            for nsdomain,nsaddr in OPENREPLICANS.iteritems():
                if dns.name.Name(nsdomain.split(".")) == question.name:
                    yield nsaddr
                    return
        else:
            for address,port in self.groups[NODE_REPLICA].get_addresses():
                yield address

    def nsresponse(self, question):
        if question.name == self.mydomain or question.name.is_subdomain(self.specialdomain):
            for address,port in self.groups[NODE_NAMESERVER].get_addresses():
                yield address+IPCONVERTER
        for subdomain in self.object.nodes.keys():
            if question.name == dns.name.Name([subdomain, 'openreplica', 'org', '']):
                for node in self.object.nodes[subdomain]:
                    yield node
        for nsdomain,nsaddr in OPENREPLICANS.iteritems():
            yield nsdomain

    def srvresponse(self, question):
        for subdomain in self.object.nodes.keys():
            if question.name == dns.name.Name(['_concoord', '_tcp', subdomain, 'openreplica', 'org', '']):
                for node in self.object.nodes[subdomain]:
                    addr,port = node.split(":")
                    yield addr+IPCONVERTER,int(port)

def main():
    nameservernode = OpenReplicaNameserver()
    nameservernode.startservice()
    signal.signal(signal.SIGINT, nameservernode.terminate_handler)
    signal.signal(signal.SIGTERM, nameservernode.terminate_handler)
    signal.pause()

if __name__=='__main__':
    main()
