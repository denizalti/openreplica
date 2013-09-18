'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Bounded semaphore proxy
@copyright: See LICENSE
'''
from concoord.blockingclientproxy import ClientProxy

class BoundedSemaphore:
    def __init__(self, bootstrap, timeout=60, debug=False, token=None):
        self.proxy = ClientProxy(bootstrap, timeout, debug, token)

    def __concoordinit__(self, count=1):
        return self.proxy.invoke_command('__init__', count)

    def __repr__(self):
        return self.proxy.invoke_command('__repr__')

    def acquire(self):
        return self.proxy.invoke_command('acquire')

    def release(self):
        return self.proxy.invoke_command('release')

    def __str__(self):
        return self.proxy.invoke_command('__str__')
