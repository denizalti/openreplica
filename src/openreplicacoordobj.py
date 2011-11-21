class OpenReplicaCoord():
    def __init__(self):
        self.nodes = {}

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

    def __str__(self):
        return str(self.nodes)
