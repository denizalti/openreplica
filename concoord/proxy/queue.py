"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Queue proxy
@copyright: See LICENSE
"""
from concoord.clientproxy import ClientProxy
class Queue:
    def __init__(self, bootstrap, timeout=60, debug=False, token=None):
        self.proxy = ClientProxy(bootstrap, timeout, debug, token)

    def __concoordinit__(self):
        return self.proxy.invoke_command('__init__')

    def append(self, item):
        return self.proxy.invoke_command('append', item)

    def remove(self):
        return self.proxy.invoke_command('remove')

    def get_size(self):
        return self.proxy.invoke_command('get_size')

    def get_queue(self):
        return self.proxy.invoke_command('get_queue')

    def __str__(self):
        return self.proxy.invoke_command('__str__')
