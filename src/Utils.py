import hashlib
import socket
import struct
#from Peer import *

# message types
# XXX separate application messages from paxi protocol message
MSG_ACCEPT, MSG_REJECT, MSG_PREPARE, MSG_PROPOSE, MSG_PERFORM, MSG_REMOVE, MSG_PING, MSG_ERROR, MSG_HELO, MSG_HELOREPLY, MSG_NEW, MSG_BYE, MSG_DEBIT, MSG_DEPOSIT, MSG_DONE, MSG_FAIL, MSG_ACK, MSG_NACK = range(1,19)

messageTypes = {1:'ACCEPT',2:'REJECT',3:'PREPARE',4:'PROPOSE',5:'PERFORM',6:'REMOVE',7:'PING',8:'ERROR',9:'HELO',\
                10:'HELOREPLY',11:'NEW',12:'BYE',13:'MSG_DEBIT',14:'MSG_DEPOSIT',15:'MSG_DONE',16:'MSG_FAIL',17:'MSG_ACK',18:'MSG_NACK'}

# STATES
LEADER_ST_INITIAL, LEADER_ST_PREPARESENT, LEADER_ST_PROPOSESENT, LEADER_ST_ACCEPTED, LEADER_ST_REJECTED = range(20,25)

# SCOUT RETURN VALUES
SCOUT_ADOPTED, SCOUT_BUSY, SCOUT_PREEMPTED = range(30,33)

# COMMANDER RETURN VALUES
COMMANDER_CHOSEN, COMMANDER_BUSY, COMMANDER_PREEMPTED = range(40,43)

replyTypes = {30:'SCOUT_ADOPTED',31:'SCOUT_BUSY',32:'SCOUT_PREEMPTED',40:'COMMANDER_CHOSEN',41:'COMMANDER_BUSY',42:'COMMANDER_PREEMPTED'}

# Lengths
MAXPROPOSALLENGTH = 20
PVALUELENGTH = 32
PEERLENGTH = 28
ADDRLENGTH = 15

# Node Types
ACCEPTOR, LEADER, REPLICA, CLIENT = range(0,4)

nodeTypes = {0:'ACCEPTOR',1:'LEADER',2:'REPLICA',3:'CLIENT'}

# Command Index
COMMANDNUMBER = 0
COMMAND = 1

# integer infinity
INFINITY = 10**100

# hashes any given string
def hash(string):
    return hashlib.md5(string).hexdigest()

def findOwnIP():
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
