import hashlib
import socket
import random
import struct
from message import *

class scoutReply():
    def __init__(self,replyLock,replyCondition,giventype=0,givenballotnumber=0,givenpvalues=[]):
        self.type = giventype
        self.ballotnumber = givenballotnumber
        self.pvalues = givenpvalues
        self.replyLock = replyLock
        self.replyCondition = replyCondition

    def setType(self,giventype):
        self.type = giventype
        
    def setBallotnumber(self,givenballotnumber):
        self.ballotnumber = givenballotnumber
        
    def setPValues(self,givenpvalues):
        self.pvalues = givenpvalues
        
    def __str__(self):
        returnstr = "Scout Reply\nType: %s\nBallotnumber: (%d,%d)\n" % (scout_names[self.type],self.ballotnumber[0],self.ballotnumber[1])
        if len(self.pvalues) > 0:
            returnstr += "Pvalues:\n"
            for pvalue in self.pvalues:
                returnstr += str(pvalue)
        return returnstr        
        
class commanderReply():
    def __init__(self,replyLock,replyCondition,giventype=0,givenballotnumber=0,givencommandnumber=0):
        self.type = giventype
        self.ballotnumber = givenballotnumber
        self.commandnumber = givencommandnumber
        self.replyLock = replyLock
        self.replyCondition = replyCondition
        
    def setType(self,giventype):
        self.type = giventype
        
    def setBallotnumber(self,givenballotnumber):
        self.ballotnumber = givenballotnumber
        
    def setCommandnumber(self,givencommandnumber):
        self.commandnumber = givencommandnumber

    def __str__(self):
        return "Commander Reply\nType: %s\nBallotnumber: (%d,%d)\nCommandnumber: %d" % (commander_names[self.type],self.ballotnumber[0],self.ballotnumber[1],self.commandnumber)
