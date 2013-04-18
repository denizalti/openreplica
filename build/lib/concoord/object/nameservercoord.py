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
        if subdomain.find('openreplica') == -1:
            subdomain = subdomain+'.openreplica.org.'
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
        if subdomain.find('openreplica') == -1:
            subdomain = subdomain+'.openreplica.org.'
        exists = subdomain in self._nodes
        if exists:
            del self._nodes[subdomain]
        return exists

    def delnodefromsubdomain(self, subdomain, nodetype, node):
        if subdomain.find('openreplica') == -1:
            subdomain = subdomain+'.openreplica.org.'
        nodetype = int(nodetype)
        exists = subdomain in self._nodes and nodetype in self._nodes[subdomain] and node in self._nodes[subdomain][nodetype]
        if exists:
            self._nodes[subdomain][nodetype].remove(node)
        return exists

    def updatesubdomain(self, subdomain, nodes):
        if subdomain.find('openreplica') == -1:
            subdomain = subdomain+'.openreplica.org.'
        if subdomain in self._nodes.keys():
            self._nodes[subdomain] = nodes
        else:
            self._nodes[subdomain] = set()
            self._nodes[subdomain] = nodes

    def getnodes(self, subdomain):
        if subdomain.find('openreplica') == -1:
            subdomain = subdomain+'.openreplica.org.'
        return self._nodes[subdomain]

    def getsubdomains(self):
        subdomains = []
        for domain in self._nodes.keys():
            subdomains.append(domain.split('.')[0])
        return subdomains

    def getdomains(self):
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
            if domain.find('openreplica') == -1:
                continue
            rstr += domain + ';('
            for nodetype, nodes in nodes.iteritems():
                if len(nodes) > 0:
                    rstr += str(nodetype) + '-' + ' '.join(nodes) + "--"
            rstr += ');'
        return rstr
