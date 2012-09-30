'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example membership object
@copyright: See LICENSE
'''
from concoord.clientproxy import ClientProxy
from threading import RLock

class Membership:
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap, token='None')

    def __concoordinit__(self, **kwargs):
        return self.proxy.invoke_command('__init__')

    def add(self, member, **kwargs):
        return self.proxy.invoke_command('add', member)

    def remove(self, member, **kwargs):
        return self.proxy.invoke_command('remove', member)

    def subscribe(self, **kwargs):
        return self.proxy.invoke_command('subscribe')

    def unsubscribe(self, **kwargs):
        return self.proxy.invoke_command('unsubscribe')

    def notifyAll(self):
        return self.proxy.invoke_command('notifyAll')

    def __str__(self, **kwargs):
        return self.proxy.invoke_command('__str__')
