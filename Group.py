from threading import RLock
from Connection import *
from Utils import *
from Peer import *

class Group():
    def __init__(self,owner):
        self.owner = owner
        self.members = []   # array of Peer()
        self.lock = RLock()

    def remove(self,peer):
        if peer in self.members:
            self.members.remove(peer)

    def add(self,peer):
        if peer == self.owner:
            return
        for oldPeer in self.members:
            if oldPeer == peer:
                return
        self.members.append(peer)
        
    def broadcast(self,msg):
        print "DEBUG: broadcasting message.."
        replies = []
        for member in self.members:
            reply = self.send_to_peer(member,msg)
            replies.append(reply)
        return replies
    
    def send_to_peer(self,peer,msg):
        print "DEBUG: sending message to " + str(peer)
        reply = ""
        message = msg.serialize()
        try:
            connection = Connection(peer.addr, peer.port)
            connection.send(msg)
            reply = connection.receive()
            connection.close()
        except Exception as inst:
            print inst     # the exception instance
            print "Error in send_to_peer."
        return reply

    def toList(self):
        return self.members
    
    def mergeList(self, list):
        for entry in list:
            self.add(entry)
    
    def __str__(self):
        returnstr = 'Members of the Group:\n'
        for member in self.members:
            returnstr += str(member)+'\n'
        return returnstr
    
    def __len__(self):
        return len(self.members)