import hashlib
import socket
import struct
from Peer import *

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
        p = Peer(peercontents[0], peercontents[1])
        neighbors.append(p)
    return neighbors

class ballotnumber():
    def __init__(self,leaderid=0,number=0):
        self.leaderid = leaderid
        self.number = number
    
    def greaterthan(self, otherballotnumber):
        if self.number > otherballotnumber.number:
            return True
        else:
            if self.leaderid > otherballotnumber.leaderid:
                return True
            else:
                return False
        
    def __str__(self):
        return 'ballotnumber(%d, %d)' % (self.leaderid, self.number)
    
class pvalue():
    def __init__(self,serialpvalue=None,ballot=0,command=0,proposal=0):
        if serialpvalue == None:
            self.ballot = ballot
            self.command = command
            self.proposal = proposal
        else:
            temp = serialpvalue
            self.ballot = struct.unpack("I", temp[0:4])[0]
            temp = temp[4:]
            self.command = struct.unpack("I", temp[0:4])[0]
            temp = temp[4:]
            self.proposal = struct.unpack("I", temp[0:4])[0]
            
    def serialize(self):
        temp = ""
        temp += struct.pack("I", self.ballot)
        temp += struct.pack("I", self.command)
        temp += struct.pack("I", self.proposal)
        return temp
        
    def __str__(self):
        return 'pvalue(%d,%d,%d)' % (self.ballot, self.command, self.proposal)
    
    def __len__(self):
        return 4*3

class Message():
    def __init__(self, serialmessage=None, type=-1, number=0, givenpvalue=0):
        if serialmessage == None:
            self.type = type
            self.number = number
            self.pvalue = givenpvalue # Data is a pvalue
            self.length = 4+4+4+len(self.pvalue)
        else:
            temp = serialmessage
            self.type = struct.unpack("I", temp[0:4])[0]
            temp = temp[4:]
            self.length = struct.unpack("I", temp[0:4])[0]
            temp = temp[4:]
            self.number = struct.unpack("I", temp[0:4])[0]
            temp = temp[4:]
            self.pvalue = pvalue(serialpvalue=temp)
        
    def serialize(self):
        temp = ""
        temp += struct.pack("I", self.type)
        temp += struct.pack("I", self.length)
        temp += struct.pack("I", self.number)
        temp += self.pvalue.serialize()
        return temp
    
    def __str__(self):
        return 'Message\n=======\nType: %d\nLength: %d\nNumber: %d\nPValue:\n%s\n' % (self.type,self.length,self.number,self.pvalue)

