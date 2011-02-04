import hashlib
import socket
import random
import struct
from message import *

def connectToBootstrap(givenpeer, bootstrap):
    bootaddr,bootport = bootstrap.split(":")
    bootid = createID(bootaddr,bootport)
    bootpeer = Peer(bootid,bootaddr,int(bootport))
    helomessage = Message(type=MSG_HELO,source=givenpeer.toPeer.serialize())
    heloreply = Message(bootpeer.sendWaitReply(helomessage))
    bootpeer = Peer(heloreply.source[0],heloreply.source[1],heloreply.source[2],heloreply.source[3])
    givenpeer.groups[bootpeer.type].add(bootpeer)
    for type,group in givenpeer.groups.iteritems():
        group.mergeList(heloreply.groups[type])

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
