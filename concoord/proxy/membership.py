'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Membership proxy
@copyright: See LICENSE
'''
from concoord.clientproxy import ClientProxy

class Membership:
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap)

    def __concoordinit__(self):
        return self.proxy.invoke_command('__init__')

    def add(self, member):
        return self.proxy.invoke_command('add', member)

    def remove(self, member):
        return self.proxy.invoke_command('remove', member)

    def __str__(self):
        return self.proxy.invoke_command('__str__')
