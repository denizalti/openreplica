'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Bank proxy
@copyright: See LICENSE
'''
from concoord.clientproxy import ClientProxy
class Bank:
    def __init__(self, bootstrap):
        self.proxy = ClientProxy(bootstrap)

    def __concoordinit__(self):
        return self.proxy.invoke_command('__concoordinit__')

    def open(self, accntno):
        return self.proxy.invoke_command('open', accntno)

    def close(self, accntno):
        return self.proxy.invoke_command('close', accntno)

    def debit(self, accntno, amount):
        return self.proxy.invoke_command('debit', accntno, amount)

    def deposit(self, accntno, amount):
        return self.proxy.invoke_command('deposit', accntno, amount)

    def balance(self, accntno):
        return self.proxy.invoke_command('balance', accntno)

    def __str__(self):
        return self.proxy.invoke_command('__str__')

