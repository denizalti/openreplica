"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Membership object to coordinate a complete mesh
@copyright: See LICENSE
"""
from threading import RLock
from concoord.exception import *
from concoord.threadingobject.drlock import DRLock

class MeshMembership():
    def __init__(self):
        self.groups = {}

    def get_group_members(self, gname):
        if gname in self.groups:
            return self.groups[gname].get_members().keys()
        else:
            raise KeyError(gname)

    def get_group_epoch(self, gname):
        if gname in self.groups:
            return self.groups[gname].get_epoch()
        else:
            raise KeyError(gname)

    def get_group_state(self, gname):
        if gname in self.groups:
            return (self.groups[gname].get_members().keys(), self.groups[gname].get_epoch())
        else:
            raise KeyError(gname)

    def add_group(self, gname, minsize):
        if gname not in self.groups:
            self.groups[gname] = Group(minsize)

    def remove_group(self, gname):
        if gname in self.groups:
            del self.groups[gname]
        else:
            raise KeyError(gname)

    def approve_join(self, gname, node, epochno):
        if gname in self.groups:
            group = self.groups[gname]
            # Check if the epoch the node wants to be
            # added to is still the current epoch.
            success = False
            if group.get_epoch() == epochno:
                # Update the epoch and members
                group.inc_epoch()
                group.add_member(node)
                # Let other members know
                group.notifyAll()
                success = True
            return (success, group.get_epoch())
        else:
            raise KeyError(gname)

    def wait(self, gname):
        if gname in self.groups:
            return self.groups[gname].wait(_concoord_command)
        else:
            raise KeyError(gname)

    def check_member(self, gname, node):
        # returns True or False and the epoch number
        if gname in self.groups:
            return (node in self.groups[gname].get_members(), self.groups[gname].get_epoch())
        else:
            raise KeyError(gname)

    def notify_failure(self, gname, epoch, failednode):
        if gname in self.groups:
            # there is a failure in the group or at least
            # one node thinks so. take a record of it
            if self.groups[gname].get_epoch() != epoch:
                return (self.groups[gname].get_members(), self.groups[gname].get_epoch())
            self.groups[gname].get_members()[failednode] += 1
            if self.groups[gname].get_members()[failednode] >= len(self.groups[gname].get_members())/2.0:
                # more than half of the nodes think that a node has failed
                # we'll change the view
                self.groups[gname].remove_member(node)
                self.groups[gname].inc_epoch()
                # notify nodes that are waiting
                self.groups[gname].notifyAll()
                return (self.groups[gname].get_members(), self.groups[gname].get_epoch())
        else:
            raise KeyError(gname)

    def __str__(self):
        return "\n".join([str(n)+': '+str(s) for n,s in self.groups.iteritems()])

class Group():
    def __init__(self, minsize):
        # Coordination
        self._epoch = 1
        self._minsize = int(minsize)
        self._members = {} # Keeps nodename:strikecount

        # Note: This is not a normal Condition object, it doesn't have
        # a lock and it doesn't provide synchronization.
        self.__waiters = [] # This will always include self.members.keys() wait commands
        self.__atomic = RLock()

    def wait(self, _concoord_command):
        # put the caller on waitinglist and take the lock away
        with self.__atomic:
            self.__waiters.append(_concoord_command)
            raise BlockingReturn()

    # This function is used only by the Coordination Object
    def notifyAll(self):
        # Notify every client on the wait list
        with self.__atomic:
            if not self.__waiters:
                return
            unblocked = {}
            for waitcommand in self.__waiters:
                # notified client should be added to the lock queue
                unblocked[waitcommand] = True
            self.__waiters = []
            raise UnblockingReturn(unblockeddict=unblocked)

    def add_member(self, member):
        if member not in self._members:
            self._members[member] = 0
            return True
        else:
            return False

    def remove_member(self, member):
        if member in self._members:
            del self._members[member]
        else:
            raise KeyError(member)

    def get_size(self):
        return self._minsize

    def get_epoch(self):
        return self._epoch

    def get_members(self):
        return self._members

    def inc_epoch(self):
        self._epoch += 1

    def __str__(self):
        t = "Epoch: %d " % self._epoch
        t += "Minimum Size: %d " % self._minsize
        t += "Members: "
        t += " ".join([str(m) for m in self._members.keys()])
        return t
