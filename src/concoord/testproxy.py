"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Automatically generated test object proxy
@copyright: See LICENSE
"""
from concoord.clientproxy import *

class Test():
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap)

    def getvalue(self):
        return self.proxy.invoke_command("getvalue", )

    def __str__(self):
        return self.proxy.invoke_command("__str__", )

