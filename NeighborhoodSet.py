from threading import RLock
from Connection import *
from utils import *

class NeighborhoodSet():
    def __init__(self):
        self.neighbors = []
        self.lock = RLock()

    def remove(self,peer):
        if peer in self.neighbors:
            self.neighbors.remove(peer)

    def add(self,peer):
        if self.ID == peer.ID:
            return
        for oldPeer in self.neighbors:
            if oldPeer.ID == peer.ID:
                return
        self.neighbors.append(peer)
        
    def broadcast(self,msg):
        print "DEBUG: broadcasting message.."
        replies = []
        for neighbor in self.neighborhoodSet.neighbors:
            reply = self.send_to_peer(neighbor.addr,neighbor.port,msg)
            if reply != "acpt":
                return None 
        return replies
    
    def send_to_peer(self,peer,msg):
        print "DEBUG: sending message to " + str(peer)
        reply = ""
        try:
            connection = Connection(peer.addr, peer.port)
            connection.send(msg)
            chunk = connection.receive()
            while (chunk != (None,None)):
                reply += chunk
                chunk = connection.receive()
            connection.close()
        except:
            print "Error in send_to_peer."
        return reply
            
    def __str__(self):
        output = ''
        for neighbor in self.neighbors:
            output += str(neighbor)+'\n'
        return output