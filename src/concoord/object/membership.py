"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example membership object
@copyright: See LICENSE
"""
from threading import RLock

class Membership():
    def __init__(self, **kwargs):
        # all members
        self.members = set()
        self.__waiters = []
        self.__atomic = RLock()

    def add(self, member, **kwargs):
        # add a member
        if member not in self.members:
            self.members.add(member)
            self.notifyAll()
        
    def remove(self, member, **kwargs):
        # remove a member
        if member in self.members:
            self.members.remove(member)
            self.notifyAll()
        else:
            raise KeyError(member)

    def subscribe(self, **kwargs):
        # subscribe to updates about the membership
        command = kwargs['_concoord_command']
        # put the caller on waitinglist and take the lock away
        with self.__atomic:
            self.__waiters.append(command)
            raise BlockingReturn()

    def unsubscribe(self, **kwargs):
        # subscribe to updates about the membership
        command = kwargs['_concoord_command']
        # put the caller on waitinglist and take the lock away
        with self.__atomic:
            self.__waiters.remove(command)

    def notifyAll(self):
        # Notify every client on the wait list
        with self.__atomic:
            if not self.__waiters:
                return
            unblocked = {}
            for waitcommand in self.__waiters:
                # notified client should be added to the lock queue
                unblocked[waitcommand] = True
            raise UnblockingReturn(unblockeddict=unblocked)

    def __str__(self, **kwargs):
        return " ".join([str(m) for m in self.members])
