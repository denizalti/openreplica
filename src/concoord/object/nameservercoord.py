'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Nameserver coordination object that keeps subdomains and their corresponding nameservers
@copyright: See LICENSE
'''
from itertools import izip

def pairwise(iterable):
    a = iter(iterable)
    return izip(a, a)

class NameserverCoord():
    def __init__(self):
        self._nodes = {} 

    def addnodetosubdomain(self, subdomain, nodetype, node):
        nodetype = int(nodetype)
        if subdomain in self._nodes:
            if nodetype in self._nodes[subdomain]:
                self._nodes[subdomain][nodetype].add(node)
            else:
                self._nodes[subdomain][nodetype] = set()
                self._nodes[subdomain][nodetype].add(node)
        else:
            self._nodes[subdomain] = {}
            self._nodes[subdomain][nodetype] = set()
            self._nodes[subdomain][nodetype].add(node)

    def delsubdomain(self, subdomain):
        exists = subdomain in self._nodes
        if exists:
            del self._nodes[subdomain]
        return exists
        
    def delnodefromsubdomain(self, subdomain, nodetype, node):
        nodetype = int(nodetype)
        exists = subdomain in self._nodes and nodetype in self._nodes[subdomain] and node in self._nodes[subdomain][nodetype]
        if exists:
            self._nodes[subdomain][nodetype].remove(node)
        return exists

    def updatesubdomain(self, subdomain, nodes):
        if subdomain in self._nodes:
            self._nodes[subdomain] = nodes
        else:
            self._nodes[subdomain] = {}
            self._nodes[subdomain] = nodes

    def getnodes(self, subdomain):
        return self._nodes[subdomain]

    def getsubdomains(self):
        return self._nodes.keys()

    def _reinstantiate(self, state):
        self._nodes = {}
        for subdomain,nodes in pairwise(state.split(';')):
            self._nodes[subdomain] = {}
            nodestypes = nodes.strip("()").split('--')
            for typeofnode in nodestypes:
                if typeofnode:
                    typename = int(typeofnode.split('-')[0])
                    self._nodes[subdomain][typename] = set()
                    nodelist = typeofnode.split('-')[1]
                    for nodename in nodelist.split():
                        self._nodes[subdomain][typename].add(nodename)

    def __str__(self):
        rstr = ''	
        for domain,nodes in self._nodes.iteritems():
            rstr += domain + ';('
            for nodetype, nodename in nodes.iteritems():
                rstr += str(nodetype) + '-' + ' '.join(nodename) + "--"
            rstr += ');'
        return rstr
