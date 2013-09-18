'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Counter proxy
@copyright: See LICENSE
'''
from concoord.clientproxy import ClientProxy

class Counter:
    def __init__(self, bootstrap, timeout=60, debug=False, token=None):
        self.proxy = ClientProxy(bootstrap, timeout, debug, token)

    def __concoordinit__(self, value=0):
        return self.proxy.invoke_command('__init__', value)

    def decrement(self):
        return self.proxy.invoke_command('decrement')

    def increment(self):
        return self.proxy.invoke_command('increment')

    def getvalue(self):
        return self.proxy.invoke_command('getvalue')

    def __str__(self):
        return self.proxy.invoke_command('__str__')
