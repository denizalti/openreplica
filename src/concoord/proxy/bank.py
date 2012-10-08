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
        return self.proxy.invoke_command('__init__')

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

class Account:
    def __init__(self, number):
        self.number = number
        self.balance = 0

    def __str__(self):
        return 'Account %s: balance = $%.2f' % (self.number, self.balance)

    def debit(self, amount):
        amount = float(amount)
        if (amount >= self.balance):
            self.balance = self.balance - amount
            return self.balance
        else:
            return False

    def deposit(self, amount):
        amount = float(amount)
        self.balance = self.balance + amount
        return self.balance
