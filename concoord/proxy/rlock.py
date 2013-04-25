'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: RLock proxy
@copyright: See LICENSE
'''
from concoord.clientproxy import ClientProxy

class RLock:
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap)

    def __concoordinit__(self):
        return self.proxy.invoke_command('__init__')

    def __repr__(self):
        return self.proxy.invoke_command('__repr__')

    def acquire(self):
        return self.proxy.invoke_command('acquire')

    def release(self):
        return self.proxy.invoke_command('release')

    def __str__(self):
        return self.proxy.invoke_command('__str__')
