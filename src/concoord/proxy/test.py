"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Automatically generated test object proxy
@copyright: See LICENSE
"""
from concoord.clientproxy import ClientProxy
from concoord.exception import ConCoordException

class Test():
    def __init__(self, bootstrap=None, connect=False):
        if connect and not bootstrap:
            raise ConCoordException("bootstrap cannot be None")
        elif connect and bootstrap:
            self.proxy = ClientProxy(bootstrap)
        else:
            return self.proxy.invoke_command('__init__', )

    def getvalue(self):
        return self.proxy.invoke_command("getvalue", )

    def __str__(self):
        return self.proxy.invoke_command("__str__", )

