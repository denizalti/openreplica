from nameserver import *

class OpenReplicaNameserver(Nameserver):
    def __init__(self, domain):
        Nameserver.__init__(self, domain=options.dnsname)
        self.nodes = {}

    def ismyname(self, name):
        return name == self.mydomain or self.ismysubdomainname(name)

    def ismysubdomainname(self, name):
        for subdomain in self.nodes.keys():
            if name == dns.name.Name([subdomain, 'openreplica', 'org', '']):
                return True
        return False
    
    def nsresponse(self, question):
        if question.name == self.mydomain:
            for address in self.groups[NODE_NAMESERVER].get_addresses():
                yield address+".foof." #XXX Can't pass only IP address
        for subdomain in self.nodes.keys():
            if name == dns.name.Name([subdomain, 'openreplica', 'org', '']):
                for node in self.nodes[subdomain]:
                    yield node
                
    def addsubdomain(self, subdomain):
         notexists = subdomain not in self.nodes
         if notexists:
            self.nodes[subdomain] = set()
         return notexists
     
    def addnodestosubdomain(self, subdomain, nodes):
        exists = subdomain in self.nodes
        if exists:
            for node in nodes:
                self.nodes[subdomain].add(node)
        return exists

    def delsubdomain(self, subdomain):
        exists = subdomain in self.nodes
        if exists:
            del self.nodes[subdomain]
        return exists
        
    def delnodesfromsubdomain(self, subdomain, nodes):
        exists = subdomain in self.nodes
        if exists:
            for node in nodes:
                self.nodes[subdomain].remove(node)
        return exists

    def getnodes(self, subdomain):
        return self.nodes[subdomain]

    def getsubdomains(self):
        return self.nodes.keys()
    
def main():
    nameservernode = OpenReplicaNameserver('openreplica.org')
    nameservernode.startservice()
    signal.signal(signal.SIGINT, nameservernode.interrupt_handler)
    signal.signal(signal.SIGTERM, nameservernode.terminate_handler)
    signal.pause()

if __name__=='__main__':
    main()
