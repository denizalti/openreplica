import hashlib
import socket
import random
import struct
from message import *

def connectToBootstrap(givenpeer, bootstrap):
    bootaddr,bootport = bootstrap.split(":")
    bootid = createID(bootaddr,bootport)
    bootpeer = Peer(bootid,bootaddr,int(bootport))
    heloMessage = Message(type=MSG_HELO,source=givenpeer.toPeer.serialize())
    heloReply = Message(bootpeer.sendWaitReply(heloMessage))
    bootpeer = Peer(heloReply.source[0],heloReply.source[1],heloReply.source[2],heloReply.source[3])
    # XXX givenpeer.buddygroups[bootpeer].add(bootpeer)
    if bootpeer.type == NODE_ACCEPTOR:
        givenpeer.acceptors.add(bootpeer)
    elif bootpeer.type == NODE_LEADER:
        givenpeer.leaders.add(bootpeer)
    else:
        givenpeer.replicas.add(bootpeer)
    givenpeer.leaders.mergeList(heloReply.leaders)
    givenpeer.acceptors.mergeList(heloReply.acceptors)
    givenpeer.replicas.mergeList(heloReply.replicas)

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
