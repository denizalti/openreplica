"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Stack proxy
@copyright: See LICENSE
"""
from concoord.clientproxy import ClientProxy
class Stack:
    def __init__(self, bootstrap, timeout=60, debug=False, token=None):
        self.proxy = ClientProxy(bootstrap, timeout, debug, token)

    def __concoordinit__(self):
        return self.proxy.invoke_command('__init__')

    def append(self, item):
        return self.proxy.invoke_command('append', item)

    def pop(self):
        return self.proxy.invoke_command('pop')

    def get_size(self):
        return self.proxy.invoke_command('get_size')

    def get_stack(self):
        return self.proxy.invoke_command('get_stack')

    def __str__(self):
        return self.proxy.invoke_command('__str__')



