"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Semaphore Coordination Object
@copyright: See LICENSE
"""
from threading import Lock
from concoord.exception import *
from concoord.enums import *

class DSemaphore():
    def __init__(self, count=1):
        if count < 0:
            raise ValueError
        self.__count = int(count)
        self.__queue = []
        self.__atomic = Lock()

    def __repr__(self):
        return "<%s count=%d>" % (self.__class__.__name__, self.__count)

    def acquire(self, _concoord_command):
        with self.__atomic:
            self.__count -= 1
            if self.__count < 0:
                self.__queue.append(_concoord_command)
                raise BlockingReturn()
            else:
                return True

    def release(self, _concoord_command):
        with self.__atomic:
            self.__count += 1
            if len(self.__queue) > 0:
                unblockcommand = self.__queue.pop(0)
                unblocked = {}
                unblocked[unblockcommand] = True
                raise UnblockingReturn(unblockeddict=unblocked)

    def __str__(self):
        return "<%s object>" % (self.__class__.__name__)
