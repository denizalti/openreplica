"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Value object proxy to test concoord implementation
@copyright: See LICENSE
"""
from concoord.clientproxy import ClientProxy

class Value():
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap, debug=False)
        
    def __concoordinit__(self):
        return self.proxy.invoke_command('__init__')

    def add_10_percent(self):
        return self.proxy.invoke_command('add_10_percent')
        
    def subtract_10000(self):
        return self.proxy.invoke_command('subtract_10000')

    def get_data(self):
        return self.proxy.invoke_command('get_data')

    def __str__(self):
        return self.proxy.invoke_command('__str__')

