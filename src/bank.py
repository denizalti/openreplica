
class Bank():
    def __init__(self):
        self.accounts = {}  # dictionary indexed by accountid storing accounts

    def cmd_openaccount(self,args):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            print "Account already exists.."
        else:
            self.accounts[accountid] = Account(accountid)
        
    def cmd_closeaccount(self, args):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            del self.accounts[accountid]
        else:
            print "Account doesn't exist.."
        
    def cmd_debit(self,args):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            self.accounts[accountid].debit()
        else:
            print "Account doesn't exist.."
        
    def cmd_deposit(self,args):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            self.accounts[accountid].deposit()
        else:
            print "Account doesn't exist.."
        
    def cmd_balance(self,args):
        accountid = args[0]
        if self.accounts.has_key(accountid):
            return self.accounts[accountid].balance
        else:
            print "Account doesn't exist.."
            return -1
    
    def __str__(self):
        temp = "**Bank**: "
        for account in self.accounts.values():
            temp += str(account)
        return temp

class Account():
    def __init__(self,id):
        self.id = id
        self.balance = 100
        self.commands = {} # dictionary indexed by commandnumber storing commands
        
    def __str__(self):
        return "Account %d: balance = %.2f" % (self.id, self.balance)
    
    def debit(self, args):
        self.balance = self.balance*0.9
        
    def deposit(self, args):
        self.balance = self.balance*1.1
        
    
        
        
