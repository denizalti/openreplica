'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Barrier proxy
@copyright: See LICENSE
'''
from concoord.clientproxy import ClientProxy

class Barrier:
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap)
        
    def __concoordinit__(self, count=1):
        return self.proxy.invoke_command('__init__', count)

    def wait(self):
        return self.proxy.invoke_command('wait')

    def __str__(self):
        return self.proxy.invoke_command('__str__')
