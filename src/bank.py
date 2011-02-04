from random import randint
from enums import *
from utils import *

class Bank():
    def __init__(self):
        self.accounts = {}  # dictionary indexed by accountid storing accounts

    def open(self,accountid):
        if self.accounts.has_key(accountid):
            print "Account already exists.."
        else:
            self.accounts[accountid] = Account(accountid)
        
    def close(self):
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
        temp = "Account %d" % self.id
        temp += "Balance: %.2f" % self.balance
        temp += "Operations:\n"
        for command in self.commands:
            temp += "\t(%d: %s)" % (command[COMMANDNUMBER],command[COMMAND])
        return temp
    
    def __eq__(self, otheraccount):
        if self.id == otheraccount.id:
            return True
        return False
    
    def debit(self):
        self.balance = self.balance*0.9
        
    def deposit(self):
        self.balance = self.balance*1.1
        
    def addCommand(self, commandnumber, command):
        if self.commands.has_key(commandnumber):
            return False
        else:
            self.commands[commandnumber] = command
            return True
        
    def removeCommand(self, commandnumber):
        del self.commands[commandnumber]

    
        
        
