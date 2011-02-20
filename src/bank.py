
class Bank():
    def __init__(self):
        self.accounts = {}  # dictionary indexed by accountid storing accounts

    def openaccount(self,args):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            print "Account already exists.."
        else:
            self.accounts[accountid] = Account(accountid)
        
    def closeaccount(self, args):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            del self.accounts[accountid]
        else:
            print "Account doesn't exist.."
        
    def debit(self,args):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            self.accounts[accountid].debit()
        else:
            print "Account doesn't exist.."
        
    def deposit(self,args):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            self.accounts[accountid].deposit()
        else:
            print "Account doesn't exist.."
        
    def balance(self,args):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            return self.accounts[accountid].balance
        else:
            print "Account doesn't exist.."
            return -1
    
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
    
    def debit(self, args):
        self.balance = self.balance*0.9
        
    def deposit(self, args):
        self.balance = self.balance*1.1
        
    
        
        
