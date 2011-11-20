from nameserver import *

class OpenReplicaNameserver(Nameserver):
    def __init__(self):
        Nameserver.__init__(self, domain='openreplica.org', instantiateobj=True)
        self.specialdomain = dns.name.Name(['ipaddr','openreplica','org',''])

    def performcore(self, msg, slotno, dometaonly=False, designated=False):
        Replica.performcore(self, msg, slotno, dometaonly, designated)

    def perform(self, msg):
        Replica.perform(self, msg)
            
    def msg_perform(self, conn, msg):
        Replica.msg_perform(self, conn, msg)

    def ismyname(self, name):
        return name == self.mydomain or name.is_subdomain(self.specialdomain) or self.ismysubdomainname(name)

    def ismysubdomainname(self, name):
        for subdomain in self.nodes.keys():
            if name == dns.name.Name([subdomain, 'openreplica', 'org', '']):
                return True
        return False

    def aresponse(self, question):
        if question.name.is_subdomain(self.specialdomain):
            yield question.name.split(4)[0].to_text()
        else:
            for gname in [NODE_LEADER, NODE_REPLICA]:
                for address in self.groups[gname].get_addresses():
                    yield address
    
    def nsresponse(self, question):
        if question.name == self.mydomain or question.name.is_subdomain(self.specialdomain):
            for address in self.groups[NODE_NAMESERVER].get_addresses():
                yield address+".ipaddr.openreplica.org."
        for subdomain in self.nodes.keys():
            if name == dns.name.Name([subdomain, 'openreplica', 'org', '']):
                for node in self.nodes[subdomain]:
                    yield node
                    
def main():
    nameservernode = OpenReplicaNameserver()
    nameservernode.startservice()
    signal.signal(signal.SIGINT, nameservernode.interrupt_handler)
    signal.signal(signal.SIGTERM, nameservernode.terminate_handler)
    signal.pause()

if __name__=='__main__':
    main()
