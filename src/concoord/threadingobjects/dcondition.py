"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Condition Coordination Object
@copyright: See LICENSE
"""
from threading import RLock
from concoord.exception import *
from concoord.threadingobjects.drlock import DRLock
    
class DCondition():
    def __init__(self, lock=None):
        if lock is None:
            lock = DRLock() #This might cause circular problems!
        self.__lock = lock
        # Export the lock's acquire() and release() methods                                                                                                           
        self.acquire = lock.acquire
        self.release = lock.release
        self.__waiters = []
        self.__atomic = RLock()

    def __repr__(self):
        return "<Condition(%s, %d)>" % (self.__lock, len(self.__waiters))

    def wait(self, kwargs):
        command = kwargs['_concoord_command']
        # put the caller on waitinglist and take the lock away
        with self.__atomic:
            if not self.__lock._isowned(command.client):
                raise RuntimeError("cannot wait on un-acquired lock")
            self.__waiters.append(command)
            self.__lock.release(kwargs)
            raise BlockingReturn()
            
    def notify(self, kwargs):
        command = kwargs['_concoord_command']
        # Notify the next client on the wait list
        with self.__atomic:
            if not self.__lock._isowned(command.client):
                raise RuntimeError("cannot wait on un-acquired lock")
            if not self.__waiters:
                return
            waitcommand = self.__waiters.pop(0)
            # To make sure that the client that will be unblocked has the lock we'll add the client to the lock queue.
            self.__lock.acquire({'_concoord_command':waitcommand}) # This in effect would Unblock the client
        
    def notifyAll(self, kwargs):
        command = kwargs['_concoord_command']
        # Notify every client on the wait list
        with self.atomic:
            if not self.__lock._isowned(command.client):
                raise RuntimeError("cannot wait on un-acquired lock")
            if not self.__waiters:
                return
            __waiters = self.__waiters
            waiters = __waiters
            for waitcommand in waiters:
                self.__lock.acquire({'_concoord_command':waitcommand}) # This in effect would Unblock the client
                try:
                    __waiters.remove(waitcommand)
                except ValueError:
                    pass
            
    def __str__(self):
        return "<%s object>" % (self.__class__.__name__)

