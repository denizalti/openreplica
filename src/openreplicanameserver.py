from nameserver import *

OPENREPLICANS = {'ns1.openreplica.org.':'128.84.60.206', 'ns2.openreplica.org.':'128.84.60.206'} 

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
        print "Creating A Response for ", question.name
        if question.name.is_subdomain(self.specialdomain):
            yield question.name.split(4)[0].to_text()
        elif self.ismynsname(question.name):
            print "It is my nsname!"
            for nsdomain,nsaddr in OPENREPLICANS.iteritems():
                if dns.name.Name(nsdomain.split(".")) == question.name:
                    yield nsaddr
                    return
        else:
            for gname in [NODE_LEADER, NODE_REPLICA]:
                for address,port in self.groups[gname].get_addresses():
                    yield address
    
    def nsresponse(self, question):
        if question.name == self.mydomain or question.name.is_subdomain(self.specialdomain):
            for address,port in self.groups[NODE_NAMESERVER].get_addresses():
                yield address+".ipaddr.openreplica.org."
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
