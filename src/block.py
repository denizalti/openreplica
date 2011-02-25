
class Block():
    def __init__(self):
        self.accounts = {}  # dictionary indexed by accountid storing accounts

    def openaccount(self, args):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            return "FAILURE"
        else:
            self.accounts[accountid] = Account(accountid)
            return "ACCT %s OPENED" % accountid
        
    def closeaccount(self, args):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            del self.accounts[accountid]
            return "ACCT %s CLOSED" % accountid
        else:
            return "FAILURE"
        
    def debit(self, args):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            self.accounts[accountid].debit()
            return "DEBIT SUCCESSFUL: %.2f" % self.accounts[accountid].balance
        else:
            return "FAILURE"
        
    def deposit(self, args):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            self.accounts[accountid].deposit()
            return "DEPOSIT SUCCESSFUL: %.2f" % self.accounts[accountid].balance
        else:
            return "FAILURE"
        
    def balance(self, args):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            return "CURRENT BALANCE: %.2f" % self.accounts[accountid].balance
        else:
            return "FAILURE"
    
    def __str__(self):
        temp = "**Bank**\n"
        for account in self.accounts.values():
            temp += str(account)+"\n"
        return temp

class Account():
    def __init__(self,id):
        self.id = id
        self.balance = 100
        self.commands = {} # dictionary indexed by commandnumber storing commands
        
    def __str__(self):
        return "Account %s: balance = %.2f" % (self.id, self.balance)
    
    def debit(self):
        self.balance = self.balance*0.9
        
    def deposit(self):
        self.balance = self.balance*1.1
        
    
        
        
