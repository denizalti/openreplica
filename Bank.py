from random import randint
from Utils import *

class Bank():
    def __init__(self):
        self.accounts = {}  # dictionary indexed by accountid storing accounts

    def openAccount(self):
        id = randint(0,100)
        while self.accounts.has_key(id):
            id = randint(0,100)
        self.accounts[id] = Account(id)
        
    def closeAccount(self):
        del self.accounts[id]
        
    def debit(self,id):
        self.accounts[id].debitTen()
        
    def deposit(self,id):
        self.accounts[id].depositTen()
        
    def balance(self,id):
        return self.accounts[id].balance
    
    def executeCommand(self,proposal):
        # The proposals are in format "ID Command": "172862 Debit"
        id,command = proposal.split(" ")
        id = int(id)
        command = command.lower()
        function = getattr(self,command)
        function(id)
        
    def __str__(self):
        temp = "Accounts:"
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
    
    def debitTen(self):
        self.balance = self.balance*0.9
        
    def depositTen(self):
        self.balance = self.balance*1.1
        
    def addCommand(self, commandnumber, command):
        if self.commands.has_key(commandnumber):
            return False
        else:
            self.commands[commandnumber] = command
            return True
        
    def removeCommand(self, commandnumber):
        del self.commands[commandnumber]

    
        
        
