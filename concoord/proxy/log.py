'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Log proxy
@copyright: See LICENSE
'''
from concoord.clientproxy import ClientProxy

class Log:
    def __init__(self, bootstrap, timeout=60, debug=False, token=None):
        self.proxy = ClientProxy(bootstrap, timeout, debug, token)

    def __concoordinit__(self):
        return self.proxy.invoke_command('__init__')

    def write(self, entry):
        return self.proxy.invoke_command('write', entry)

    def append(self, entry):
        return self.proxy.invoke_command('append', entry)

    def read(self):
        return self.proxy.invoke_command('read')

    def __str__(self):
        return self.proxy.invoke_command('__str__')
