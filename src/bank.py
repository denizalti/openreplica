
class Bank():
    def __init__(self):
        self.accounts = {}  # dictionary indexed by accountid storing accounts

    def openaccount(self,accountid):
        if self.accounts.has_key(accountid):
            print "Account already exists.."
        else:
            self.accounts[accountid] = Account(accountid)
        
    def closeaccount(self):
        if self.accounts.has_key(accountid):
            del self.accounts[accountid]
        else:
            print "Account doesn't exist.."
        
    def debit(self,id):
        if self.accounts.has_key(accountid):
            self.accounts[id].debit()
        else:
            print "Account doesn't exist.."
        
    def deposit(self,id):
        if self.accounts.has_key(accountid):
            self.accounts[id].deposit()
        else:
            print "Account doesn't exist.."
        
    def balance(self,id):
        if self.accounts.has_key(accountid):
            return self.accounts[id].balance
        else:
            print "Account doesn't exist.."
            return -1
    
    def executeCommand(self,proposal):
        command,accountid = proposal.split(" ")
        accountid = int(accountid)
        command = command.lower()
        function = getattr(self,command)
        function(accountid)
        
    def __str__(self):
        temp = "**Bank**"
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
    
    def debit(self):
        self.balance = self.balance*0.9
        
    def deposit(self):
        self.balance = self.balance*1.1
        
    
        
        
