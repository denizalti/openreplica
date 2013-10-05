"""
@author: Deniz Altinbuken, Emin Gun Sirer
"""
from concoord.clientproxy import ClientProxy

class Test():
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap, True)

    def __concoordinit__(self):
        return self.proxy.invoke_command('__init__')

    def write(self, entry):
        return self.proxy.invoke_command('write', entry)

    def append(self, entry):
        return self.proxy.invoke_command('append', entry)

    def write(self):
        return self.proxy.invoke_command('read')

    def __str__(self):
        return self.proxy.invoke_command('__str__')

