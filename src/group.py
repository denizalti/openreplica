"""
@author: denizalti
@note: Group
@date: February 1, 2011
"""
from threading import RLock
from connection import *
from enums import *
from utils import *
from peer import *
from message import *

class Group():
    """Group keeps a set of Peer objects and supports functions
    related to a Group object.
    """
    def __init__(self,owner):
        """Initialize Group

        Group State
        - owner: Peer that owns the Group
        - members: set of Peers that are in the Group
        """
        self.owner = owner
        self.members = set()

    def remove(self,peer):
        """Removes the given peer from the Group"""
        if peer in self.members:
            self.members.remove(peer)

    def add(self,peer):
        """Adds the given peer to the Group if it's not the owner itself"""
        if peer != self.owner:
            self.members.add(peer)

    def union(self,othergroup):
        """Unionizes the members of given Group with the members of the Group"""
        for peer in othergroup.members:
            if peer != self.owner:
                self.members.add(peer)
        
    def broadcast(self,sendernode,msg):
        """Broadcasts the given message to the members of the Group"""
        for member in self.members:
            member.send(sendernode,msg)

    def __str__(self):
        """Returns Group information"""
        returnstr = ''
        for member in self.members:
            returnstr += str(member)+' '
        return returnstr
    
    def __len__(self):
        """Returns number of Peers in the Group"""
        return len(self.members)
