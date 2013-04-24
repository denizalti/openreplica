'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Log proxy
@copyright: See LICENSE
'''
from concoord.clientproxy import ClientProxy

class Log:
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap)

    def __concoordinit__(self):
        return self.proxy.invoke_command('__concoordinit__')

    def write(self, entry):
        return self.proxy.invoke_command('write', entry)

    def append(self, entry):
        return self.proxy.invoke_command('append', entry)

    def read(self):
        return self.proxy.invoke_command('read')

    def __str__(self):
        return self.proxy.invoke_command('__str__')
