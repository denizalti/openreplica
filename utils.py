import hashlib
import socket
import struct
#from Peer import *

INFINITY = float('inf')

# Message Types
ACCEPT = 0
REJECT = 1
PREPARE = 2
PROPOSE = 3
DONE = 4
REMOVE = 5
PING = 6
ERROR = 7
HELO = 8

# STATES
LEADER_ST_INITIAL = 20
LEADER_ST_PREPARESENT = 21
LEADER_ST_PROPOSESENT = 22
LEADER_ST_ACCEPTED = 23
LEADER_ST_REJECTED = 24

# Lengths
MAXPROPOSALLENGTH = 20
PVALUELENGTH = 32

# This function hashes any given string
def hash(name):
    return hashlib.md5(name).hexdigest()

def findOwnIP():
#    return socket.gethostbyname(socket.gethostname())
    return socket.gethostbyname(socket.gethostname())

# This function computes a NodeID given an addr and port
def computeNodeID(addr, port):
    name = addr+str(port)
    return hash(name)

def from_str_to_dict(self, string):
    string = string.rstrip("-")
    items = [s for s in string.split("-") if s]
    dictionary = {}
    for item in items:
        key,value = item.split("/")
        dictionary[key] = value
    return dictionary
    
def from_dict_to_str(self, dictionary):
    string = ""
    for key in dictionary:
        string += key + "/" + str(dictionary[key]) + "-"
    return string

def from_neighbors_to_str(self, neighbor_list):
    liststr = ''
    for peer in neighbor_list:
        peerstr = "%s:%d:%s" % (peer.addr, peer.port, peer.ID)
        liststr = liststr + "/" + peerstr
    return liststr

def from_str_to_neighbors(self, string):
    neighbors = []
    string = string.rstrip("/")
    peers = string.split("/")
    for peer in peers:
        peercontents = peer.split(":")
        #p = Peer(peercontents[0], peercontents[1])
        #neighbors.append(p)
    return neighbors
    
class pvalue():
    def __init__(self,serialpvalue=None,ballotnumber=(0,0),commandnumber=0,proposal=""):
        if serialpvalue == None:
            self.ballotnumber = ballotnumber
            self.commandnumber = commandnumber
            self.proposal = proposal
        else:
            temp = serialpvalue
            self.ballotnumber = struct.unpack("II", temp[0:8])
            temp = temp[8:]
            self.commandnumber = struct.unpack("I", temp[0:4])[0]
            temp = temp[4:]
            self.proposal = struct.unpack("20s",temp)[0]
            
    def serialize(self):
        temp = ""
        temp += struct.pack("II", self.ballotnumber[0],self.ballotnumber[1])
        temp += struct.pack("I", self.commandnumber)
        temp += struct.pack("20s", self.proposal)
        return temp
        
    def __str__(self):
        return 'pvalue((%d,%d),%d,%s)' % (self.ballotnumber[0],self.ballotnumber[1],self.commandnumber,self.proposal.strip("\x00"))

class Message():
    def __init__(self, serialmessage=None, type=-1, givenpvalues=[]):
        if serialmessage == None:
            self.type = type
            self.numpvalues = len(givenpvalues)
            self.pvalues = givenpvalues
            self.length = 12+self.numpvalues*PVALUELENGTH
        else:
            temp = serialmessage
            self.type = struct.unpack("I", temp[0:4])[0]
            temp = temp[4:]
            self.length = struct.unpack("I", temp[0:4])[0]
            temp = temp[4:]
            self.numpvalues = struct.unpack("I", temp[0:4])[0]
            temp = temp[4:]
            self.pvalues = []
            for i in range(0,self.numpvalues):
                self.pvalues.append(pvalue(temp[0:32]))
                temp = temp[32:]
        
    def serialize(self):
        temp = ""
        temp += struct.pack("I", self.type)
        temp += struct.pack("I", self.length)
        temp += struct.pack("I", self.numpvalues)
        for i in range(0,self.numpvalues):
                temp += self.pvalues[i].serialize()
        return temp
    
    def __str__(self):
        temp = 'Message\n=======\nType: %d\nLength: %d\nPValues:\n' % (self.type,self.length)
        for i in range(0,self.numpvalues):
            temp += str(self.pvalues[i]) + '\n'
        return temp

