"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Value object proxy to test concoord implementation
@copyright: See LICENSE
"""
from concoord.clientproxy import ClientProxy

class Test():
    def __init__(self, bootstrap, timeout=60, debug=False, token=None):
        self.proxy = ClientProxy(bootstrap, timeout, debug, token)

    def __concoordinit__(self):
        return self.proxy.invoke_command('__init__')

    def getvalue(self):
        return self.proxy.invoke_command('getvalue')

    def setvalue(self, newvalue):
        return self.proxy.invoke_command('setvalue', newvalue)

    def __str__(self):
        return self.proxy.invoke_command('__str__')

