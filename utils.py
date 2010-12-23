import hashlib
import socket
from Peer import *

INFINITY = float('inf')

# This function hashes any given string
def hash(name):
    return hashlib.md5(name).hexdigest()

def findOwnIP():
#    return socket.gethostbyname(socket.gethostname())
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('google.com', 0))
    return s.getsockname()[0]

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



