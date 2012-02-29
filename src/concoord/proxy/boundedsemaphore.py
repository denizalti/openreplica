'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: BoundedSemaphore proxy
@copyright: LICENSE
'''
from concoord.clientproxy import ClientProxy

class BoundedSemaphore:
    def __init__(self, bootstrap, count=1):
        self.proxy = ClientProxy(bootstrap)
        return self.proxy.invoke_command('__init__', count)

    def __repr__(self):
        return self.proxy.invoke_command('__repr__')

    def acquire(self):
        return self.proxy.invoke_command('acquire')

    def release(self):
        return self.proxy.invoke_command('release')

    def __str__(self):
        return self.proxy.invoke_command('__str__')
