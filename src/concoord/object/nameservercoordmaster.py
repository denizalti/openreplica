'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Nameserver coordination object that keeps subdomains and their corresponding nameservers
@copyright: See LICENSE
'''
class NameserverCoord():
    def __init__(self, **kwargs):
        self.nodes = {} # slave domainname to answertypes

    def addanswertosubdomain(self, subdomain, answer, answertype **kwargs):
        if subdomain in self.nodes:
            self.nodes[subdomain][answertype] = answer
        else:
            self.nodes[subdomain] = {}
            self.nodes[subdomain][answertype] = answer

    def delsubdomain(self, subdomain, **kwargs):
        exists = subdomain in self.nodes
        if exists:
            del self.nodes[subdomain]
        return exists

    def getsubdomains(self, **kwargs):
        return self.nodes.keys()

    def _reinstantiatefromstr(self, state, **kwargs):
        #XXX
        self.nodes = {}
        for subdomain in state.split('-'):
            if subdomain != '':
                subdomainname, subdomainitems = subdomain.split(':')
                self.nodes[subdomainname] = set(subdomainitems.split(''))

    def __str__(self, **kwargs):
        #XXX
        rstr = ''	
        for domain,nodes in self.nodes.iteritems():
            rstr += domain + ';' + ' '.join(nodes) + "-"
        return rstr
