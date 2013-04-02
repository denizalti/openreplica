"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Value object proxy to test concoord implementation
@copyright: See LICENSE
"""
from concoord.asyncclientproxy import ClientProxy

class Test():
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap, True)

    def __concoordinit__(self):
        reqdesc = self.proxy.invoke_command_async('__init__')
        return self.proxy.wait_until_command_done(reqdesc)

    def getvalue(self):
        reqdesc = self.proxy.invoke_command_async('getvalue')
        return self.proxy.wait_until_command_done(reqdesc)

    def setvalue(self, newvalue):
        reqdesc = self.proxy.invoke_command_async('setvalue', newvalue)
        return self.proxy.wait_until_command_done(reqdesc)

    def __str__(self):
        reqdesc = self.proxy.invoke_command_async('__str__')
        return self.proxy.wait_until_command_done(reqdesc)
