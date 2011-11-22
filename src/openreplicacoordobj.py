class OpenReplicaCoord():
    def __init__(self, **kwargs):
        self.nodes = {}

    def addsubdomain(self, subdomain, **kwargs):
        notexists = subdomain not in self.nodes
        if notexists:
            self.nodes[subdomain] = set()
        return notexists
     
    def addnodetosubdomain(self, subdomain, node, **kwargs):
        exists = subdomain in self.nodes
        if exists:
            self.nodes[subdomain].add(node)
        return exists

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

    def __str__(self, **kwargs):
        return str(self.nodes)
