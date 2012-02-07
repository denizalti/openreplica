'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: OpenReplica coordination object that keeps subdomains and their corresponding nameservers
@date: August 1, 2011
@copyright: See COPYING.txt
'''
class OpenReplicaCoord():
    def __init__(self, **kwargs):
        self.nodes = {}

    def addnodetosubdomain(self, subdomain, node, **kwargs):
        if subdomain in self.nodes:
            self.nodes[subdomain].add(node)
        else:
            self.nodes[subdomain] = set()
            self.nodes[subdomain].add(node)

    def delsubdomain(self, subdomain, **kwargs):
        exists = subdomain in self.nodes
        if exists:
            del self.nodes[subdomain]
        return exists
        
    def delnodefromsubdomain(self, subdomain, node, **kwargs):
        exists = subdomain in self.nodes
        if exists:
            self.nodes[subdomain].remove(node)
        return exists

    def getnodes(self, subdomain, **kwargs):
        return self.nodes[subdomain]

    def getsubdomains(self, **kwargs):
        return self.nodes.keys()

    def _reinstantiatefromstr(self, state, **kwargs):
        self.nodes = {}
        for subdomain in state.split('-'):
            if subdomain != '':
                subdomainname, subdomainitems = subdomain.split(':')
                self.nodes[subdomainname] = set(subdomainitems.split(''))

    def __str__(self, **kwargs):
        rstr = ''	
        for domain,nodes in self.nodes.iteritems():
            rstr += domain + ';' + ' '.join(nodes) + "-"
        return rstr
