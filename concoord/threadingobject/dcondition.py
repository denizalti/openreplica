"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Condition Coordination Object
@copyright: See LICENSE
"""
from threading import RLock
from concoord.exception import *
from concoord.threadingobject.drlock import DRLock

class DCondition():
    def __init__(self, lock=None):
        if lock is None:
            lock = DRLock()
        self.__lock = lock
        # Export the lock's acquire() and release() methods
        self.acquire = lock.acquire
        self.release = lock.release
        self.__waiters = []
        self.__atomic = RLock()

    def __repr__(self):
        return "<Condition(%s, %d)>" % (self.__lock, len(self.__waiters))

    def wait(self, _concoord_command):
        # put the caller on waitinglist and take the lock away
        with self.__atomic:
            if not self.__lock._is_owned(_concoord_command.client):
                raise RuntimeError("cannot wait on un-acquired lock")
            self.__waiters.append(_concoord_command)
            self.__lock.release(_concoord_command)
            raise BlockingReturn()

    def notify(self, _concoord_command):
        # Notify the next client on the wait list
        with self.__atomic:
            if not self.__lock._is_owned(_concoord_command.client):
                raise RuntimeError("cannot notify on un-acquired lock")
            if not self.__waiters:
                return
            waitcommand = self.__waiters.pop(0)
            # notified client should be added to the lock queue
            self.__lock._add_to_queue(waitcommand)

    def notifyAll(self, _concoord_command):
        # Notify every client on the wait list
        with self.__atomic:
            if not self.__lock._is_owned(_concoord_command.client):
                raise RuntimeError("cannot notify on un-acquired lock")
            if not self.__waiters:
                return
            for waitcommand in self.__waiters:
                # notified client should be added to the lock queue
                self.__lock._add_to_queue(waitcommand)
            self.__waiters = []

    def __str__(self):
        return "<%s object>" % (self.__class__.__name__)

