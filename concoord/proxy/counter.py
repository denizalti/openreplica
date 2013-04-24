'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Counter proxy
@copyright: See LICENSE
'''
from concoord.clientproxy import ClientProxy

class Counter:
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap)

    def __concoordinit__(self):
        return self.proxy.invoke_command('__concoordinit__')

    def decrement(self):
        return self.proxy.invoke_command('decrement')

    def increment(self):
        return self.proxy.invoke_command('increment')

    def getvalue(self):
        return self.proxy.invoke_command('getvalue')

    def __str__(self):
        return self.proxy.invoke_command('__str__')
