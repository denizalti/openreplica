class Bank():
    """Bank object that supports following functions:
    - open: creates an Account with given id
    - close: deletes an Account with given id
    - debit: debits money from Account with given id
    - deposit: deposits to Account with given id
    - balance: returns balance of Account with given id
    """
    def __init__(self):
        self.accounts = {}  # dictionary indexed by accountid storing accounts

    def open(self, args, **kwargs):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            return False
        else:
            self.accounts[accountid] = Account(accountid)
            return True
        
    def close(self, args, **kwargs):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            del self.accounts[accountid]
            return True
        else:
            return False #XXX raise KeyError
        
    def debit(self, args, **kwargs):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            self.accounts[accountid].debit()
            return self.accounts[accountid].balance
        else:
            return False #XXX raise KeyError
        
    def deposit(self, args, **kwargs):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            self.accounts[accountid].deposit()
            return self.accounts[accountid].balance
        else:
            return False #XXX raise KeyError
        
    def balance(self, args, **kwargs):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            return self.accounts[accountid].balance
        else:
            return False #XXX raise KeyError
    
    def __str__(self):
        return "\n".join(["%s" % (str(account)) for account in self.accounts.values()])

class Account():
    def __init__(self, id):
        self.id = id
        self.balance = 100
        
    def __str__(self):
        return "Account %s: balance = %.2f" % (self.id, self.balance)
    
    def debit(self):
        self.balance = self.balance*0.9
        
    def deposit(self):
        self.balance = self.balance*1.1
        
    
        
        
