import hashlib
import socket
import random
import struct

# message types
# XXX separate application messages from paxi protocol message
MSG_ACCEPT, MSG_REJECT, MSG_PREPARE, MSG_PROPOSE, MSG_PERFORM, MSG_REMOVE, MSG_PING, MSG_ERROR, MSG_HELO, MSG_HELOREPLY,\
            MSG_NEW, MSG_BYE, MSG_DEBIT, MSG_DEPOSIT, MSG_OPEN, MSG_CLOSE, MSG_DONE, MSG_FAIL = range(18)

messageTypes = ['ACCEPT','REJECT','PREPARE','PROPOSE','PERFORM','REMOVE','PING','ERROR','HELO','HELOREPLY','NEW','BYE',\
                'MSG_DEBIT','MSG_DEPOSIT','OPEN','CLOSE','MSG_DONE','MSG_FAIL']

# STATES
# LEADER_ST_INITIAL, LEADER_ST_PREPARESENT, LEADER_ST_PROPOSESENT, LEADER_ST_ACCEPTED, LEADER_ST_REJECTED = range(5)

# SCOUT RETURN VALUES
NOREPLY, SCOUT_ADOPTED, SCOUT_BUSY, SCOUT_PREEMPTED, COMMANDER_CHOSEN, COMMANDER_BUSY, COMMANDER_PREEMPTED = range(7)
replyTypes = ['NOREPLY', 'SCOUT_ADOPTED','SCOUT_BUSY','SCOUT_PREEMPTED','COMMANDER_CHOSEN','COMMANDER_BUSY','COMMANDER_PREEMPTED']

# Lengths
MAXPROPOSALLENGTH = 20
PVALUELENGTH = 32
PEERLENGTH = 28
ADDRLENGTH = 15

# Node Types
ACCEPTOR, LEADER, REPLICA, CLIENT = range(0,4)
nodeTypes = ['ACCEPTOR','LEADER','REPLICA','CLIENT']

# Command Index
COMMANDNUMBER = 0
COMMAND = 1

# integer infinity
INFINITY = 10**100

def createID(addr,port):
    random.seed(addr+str(port))
    return random.randint(0, 1000000)

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
