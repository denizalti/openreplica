'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: OpenReplica coordination object proxy
@copyright: LICENSE
'''
from concoord.clientproxy import ClientProxy

class OpenReplicaCoord():
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap)
        return self.proxy.invoke_command('__init__')

    def addnodetosubdomain(self, subdomain, node):
        return self.proxy.invoke_command("addnodetosubdomain", subdomain, node)

    def delnodefromsubdomain(self, subdomain, node):
        return self.proxy.invoke_command("delnodefromsubdomain", subdomain, node)

    def delsubdomain(self, subdomain):
        return self.proxy.invoke_command("delsubdomain", subdomain)

    def getnodes(self, subdomain):
        return self.proxy.invoke_command("getnodes", subdomain)

    def getsubdomains(self):
        return self.proxy.invoke_command("getsubdomains")

    def __str__(self):
        return self.proxy.invoke_command("__str__")
