'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Barrier proxy
@copyright: LICENSE
'''
from concoord.clientproxy import ClientProxy

class Barrier:
    def __init__(self, bootstrap, count=1):
        self.proxy = ClientProxy(bootstrap)
        return self.proxy.invoke_command('__init__', count)

    def wait(self):
        return self.proxy.invoke_command('wait')

    def __str__(self):
        return self.proxy.invoke_command('__str__')
