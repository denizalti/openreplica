'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example semaphore object
@copyright: See LICENSE
'''
from concoord.clientproxy import ClientProxy

class Semaphore:
    def __init__(self, count=1, bootstrap=None, connect=False):
        self.proxy = ClientProxy(bootstrap)
        if not connect:
            return self.proxy.invoke_command('__init__', count)
    
    def __repr__(self):
        return self.proxy.invoke_command('__repr__')

    def acquire(self):
        return self.proxy.invoke_command('acquire')

    def release(self):
        return self.proxy.invoke_command('release')

    def __str__(self):
        return self.proxy.invoke_command('__str__')
