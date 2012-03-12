'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Nameserver coordination object that keeps subdomains and their corresponding nameservers
@copyright: See LICENSE
'''
class NameserverCoord():
    def __init__(self, **kwargs):
        self.nodes = {} # slave domainname to answertypes

    def update_slave_subdomain(self, subdomain **kwargs):
        if subdomain in self.slaves:
            self.slaves[subdomain][answertype] = answer
        else:
            self.slaves[subdomain] = {}
            self.slaves[subdomain][answertype] = answer

    def delete_slave_subdomain(self, subdomain, **kwargs):
        exists = subdomain in self.slaves
        if exists:
            del self.slaves[subdomain]
        return exists

    def get_slave_subdomains(self, **kwargs):
        return self.slaves.keys()

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
