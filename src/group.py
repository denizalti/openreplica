from threading import RLock
from connection import *
from enums import *
from utils import *
from peer import *
from message import *

class Group():
    def __init__(self,owner):
        self.owner = owner
        self.members = set()

    def remove(self,peer):
        if peer in self.members:
            self.members.remove(peer)

    def add(self,peer):
        if peer != self.owner:
            print peer
            self.members.add(peer)

    def union(self,othergroup):
        for peer in othergroup.members:
            if peer != self.owner:
                self.members.add(peer)
        
    def broadcast(self,sendernode,msg):
#        print "[%s]: broadcasting message" % sendernode
        replies = []
        # XXX not very efficient, does not have a timeout
        # need to send to everyone at the same time, then collect
        # responses as they come back
        for member in self.members:
            reply = member.sendWaitReply(sendernode,msg)
            replies.append(reply)
        return replies
    
    def broadcastNoReply(self,msg):
#        print "DEBUG: broadcasting message.."
        for member in self.members:
            member.send(msg)

    def __str__(self):
        returnstr = ''
        for member in self.members:
            returnstr += str(member)+' '
        return returnstr
    
    def __len__(self):
        return len(self.members)
