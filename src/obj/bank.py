import sys

class Bank():
    def __init__(self):
        self.accounts = {}

    def dene(self, args):
        dene = 'w'
        f = open('/deneme', dene)

    def open(self, args, **kwargs):
        accntno = args[0]
        if self.accounts.has_key(accntno):
            return False
        else:
            self.accounts[accntno] = Account(accntno)
            return True
        
    def close(self, args, **kwargs):
        accntno = args[0]
        if self.accounts.has_key(accntno):
            del self.accounts[accntno]
            return True
        else:
            raise KeyError
        
    def debit(self, args, **kwargs):
        accntno, amount = args
        if self.accounts.has_key(accntno):
            return self.accounts[accntno].debit(amount)
        else:
            raise KeyError
        
    def deposit(self, args, **kwargs):
        accntno, amount = args
        if self.accounts.has_key(accntno):
            return self.accounts[accntno].deposit(amount)
        else:
            raise KeyError
        
    def balance(self, args, **kwargs):
        accntno = args[0]
        if self.accounts.has_key(accntno):
            return self.accounts[accntno].balance
        else:
            raise KeyError
    
    def __str__(self):
        return "\n".join(["%s" % (str(account)) for account in self.accounts.values()])

class Account():
    def __init__(self, number):
        self.number = number
        self.balance = 0
        
    def __str__(self):
        return "Account %s: balance = $%.2f" % (self.id, self.balance)
    
    def debit(self, amount):
        amount = float(amount)
        if amount >= self.balance:
            self.balance = self.balance - amount
            return self.balance
        else:
            return False
        
    def deposit(self, amount):
        amount = float(amount)
        self.balance = self.balance + amount
        return self.balance
        
    
        
        
