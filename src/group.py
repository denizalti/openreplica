"""
@author: denizalti, egs
@note: Group
@date: February 1, 2011
"""
from threading import RLock
from connection import *
from enums import *
from utils import *
from peer import *

class Group():
    """A Group is a collection of Peers that perform the same function."""
    def __init__(self,owner):
        """
        - owner: Peer that owns the Group
        - members: set of Peers that are in the Group
        """
        self.owner = owner
        self.members = []

    def remove(self,peer):
        """Removes the given peer from the Group."""
        if peer in self.members:
            self.members.remove(peer)
            self.members.sort()

    def add(self,peer):
        """Adds the given peer to the Group if it's not the owner itself."""
        if peer != self.owner:
            if peer not in self.members:
                self.members.append(peer)
                self.members.sort()

    def union(self,othergroup):
        """Adds the given Group to this one."""
        for peer in othergroup.members:
            if peer not in self.members:
                self.members.append(peer)
        self.members.sort()

    def haspeer(self,peer):
        return peer in self.members

    def get_addresses(self):
        for peer in self.members:
            yield (peer.addr,peer.port)

    def __iter__(self):
        for peer in self.members:
            yield peer

    def __str__(self):
        """Returns Group information"""
        return " ".join(str(peer) for peer in self.members)
    
    def __len__(self):
        """Returns number of Peers in the Group"""
        return len(self.members)
