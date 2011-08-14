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
            return "ACCT %s ALREADY EXISTS" % accountid
        else:
            self.accounts[accountid] = Account(accountid)
            return "ACCT %s OPENED" % accountid
        
    def close(self, args, **kwargs):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            del self.accounts[accountid]
            return "ACCT %s CLOSED" % accountid
        else:
            return "ACCT %s DOES NOT EXIST" % accountid
        
    def debit(self, args, **kwargs):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            self.accounts[accountid].debit()
            return "DEBIT SUCCESSFUL: %.2f" % self.accounts[accountid].balance
        else:
            return "ACCT %s DOES NOT EXIST" % accountid
        
    def deposit(self, args, **kwargs):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            self.accounts[accountid].deposit()
            return "DEPOSIT SUCCESSFUL: %.2f" % self.accounts[accountid].balance
        else:
            return "ACCT %s DOES NOT EXIST" % accountid
        
    def balance(self, args, **kwargs):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            return "CURRENT BALANCE: %.2f" % self.accounts[accountid].balance
        else:
            return "ACCT %s DOES NOT EXIST" % accountid
    
    def __str__(self):
        temp = "BANK\n"
        for account in self.accounts.values():
            temp += str(account)+"\n"
        return temp

class Account():
    def __init__(self, id):
        self.id = id
        self.balance = 100
        self.commands = {} # dictionary indexed by commandnumber storing commands
        
    def __str__(self):
        return "Account %s: balance = %.2f" % (self.id, self.balance)
    
    def debit(self):
        self.balance = self.balance*0.9
        
    def deposit(self):
        self.balance = self.balance*1.1
        
    
        
        
