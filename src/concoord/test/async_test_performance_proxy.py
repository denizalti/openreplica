"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Value object proxy to test concoord implementation
@copyright: See LICENSE
"""
from concoord.asyncclientproxy import ClientProxy

class Test():
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap, True)

    def __concoordinit__(self):
        cno,condition = self.proxy.invoke_command_async('__init__')
        with ccond:
            while not self.proxy.command_done_async(cno)[0]:
                ccond.wait()

    def getvalue(self):
        cno,ccond = self.proxy.invoke_command_async('getvalue')
        with ccond:
            while not self.proxy.command_done_async(cno)[0]:
                ccond.wait()

    def setvalue(self, newvalue):
        cno,condition = self.proxy.invoke_command_async('setvalue', newvalue)
        with ccond:
            while not self.proxy.command_done_async(cno)[0]:
                ccond.wait()

    def __str__(self):
        cno,condition = self.proxy.invoke_command_async('__str__')
        with ccond:
            while not self.proxy.command_done_async(cno)[0]:
                ccond.wait()
