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
#        print "DEBUG: broadcasting message.."
        replies = []
        for member in self.members:
            reply = self.sendToPeer(member,msg)
            replies.append(reply)
        return replies
    
    def sendToPeer(self,peer,msg):
#        print "DEBUG: sending message to " + str(peer)
        reply = ""
        message = msg.serialize()
        connection = Connection(peer.addr, peer.port)
        connection.send(msg)
        if msg.type != MSG_BYE:
            reply = connection.receive()
        connection.close()
        return reply

    def toList(self):
        return self.members
    
    def mergeList(self, list):
        for entry in list:
            self.add(entry)
    
    def __str__(self):
        returnstr = ''
        for member in self.members:
            returnstr += str(member)+'\n'
        return returnstr
    
    def __len__(self):
        return len(self.members)