import hashlib
import socket
import struct
#from Peer import *

INFINITY = float('inf')

# MSGS
MSG_ACCEPT = 1
MSG_REJECT = 2
MSG_PREPARE = 3
MSG_PROPOSE = 4
MSG_PERFORM = 5
MSG_REMOVE = 6
MSG_PING = 7
MSG_ERROR = 8
MSG_HELO = 9
MSG_HELOREPLY = 10
MSG_NEW = 11
MSG_BYE = 12
MSG_DEBIT = 13
MSG_DEPOSIT = 14
MSG_DONE = 15
MSG_FAIL = 16

messageTypes = {1:'ACCEPT',2:'REJECT',3:'PREPARE',4:'PROPOSE',5:'PERFORM',6:'REMOVE',7:'PING',8:'ERROR',9:'HELO',10:'HELOREPLY',11:'NEW',12:'BYE'}

# STATES
LEADER_ST_INITIAL = 20
LEADER_ST_PREPARESENT = 21
LEADER_ST_PROPOSESENT = 22
LEADER_ST_ACCEPTED = 23
LEADER_ST_REJECTED = 24

# SCOUT RETURN VALUES
SCOUT_ADOPTED = 30
SCOUT_BUSY = 31
SCOUT_PREEMPTED = 32

# COMMANDER RETURN VALUES
COMMANDER_CHOSEN = 40
COMMANDER_BUSY = 41
COMMANDER_PREEMPTED = 42

replyTypes = {30:'SCOUT_ADOPTED',31:'SCOUT_BUSY',32:'SCOUT_PREEMPTED',40:'COMMANDER_CHOSEN',41:'COMMANDER_BUSY',42:'COMMANDER_PREEMPTED'}

# Lengths
MAXPROPOSALLENGTH = 20
PVALUELENGTH = 32
PEERLENGTH = 28
ADDRLENGTH = 15

# Node Types
ACCEPTOR = 0 
LEADER = 1
REPLICA = 2
CLIENT = 3

# This function hashes any given string
def hash(name):
    return hashlib.md5(name).hexdigest()

def findOwnIP():
#    return socket.gethostbyname(socket.gethostname())
    return socket.gethostbyname(socket.gethostname())

# pvalue calculations
# Returns the union of two pvalue arrays
def union(pvalues1, pvalues2):
    for pvalue in pvalues2:
        if pvalue in pvalues1:
            pass
        else:
            pvalues1.append(pvalue)
    return pvalues1

# Returns the max of a pvalue array            
def max(pvalues):
    maxpvalue = pvalue(ballotnumber=(0,0),commandnumber=0,proposal="")
    for pvalue in pvalues:
        if pvalue > maxpvalue:
            maxpvalue = pvalue
    return maxpvalue

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
        print "+++++++++++++++++++++++++++++"
        print self.pvalues
        returnstr = "Scout Reply\nType: %s\nBallotnumber: (%d,%d)\n" % (replyTypes[self.type],self.ballotnumber[0],self.ballotnumber[1])
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
        return "Commander Reply\nType: %s\nBallotnumber: (%d,%d)\nCommandnumber: %d" % (replyTypes[self.type],self.ballotnumber[0],self.ballotnumber[1],self.commandnumber)