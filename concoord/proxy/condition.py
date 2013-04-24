'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Condition proxy
@copyright: See LICENSE
'''
from concoord.clientproxy import ClientProxy

class Condition:
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap)

    def __concoordinit__(self, lock=None):
        return self.proxy.invoke_command('__concoordinit__', lock)

    def __repr__(self):
        return self.proxy.invoke_command('__repr__')

    def acquire(self):
        return self.proxy.invoke_command('acquire')

    def release(self):
        return self.proxy.invoke_command('release')

    def wait(self):
        return self.proxy.invoke_command('wait')

    def notify(self):
        return self.proxy.invoke_command('notify')

    def notifyAll(self):
        return self.proxy.invoke_command('notifyAll')

    def __str__(self):
        return self.proxy.invoke_command('__str__')
