"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Lock Coordination Object
@copyright: See LICENSE
"""
from threading import Lock
from concoord.enums import *
from concoord.exception import *

class DLock():
    def __init__(self):
        self.__locked = False
        self.__owner = None
        self.__queue = []
        self.__atomic = Lock()

    def __repr__(self):
        return "<%s owner=%s>" % (self.__class__.__name__, str(self.__owner))

    def acquire(self, _concoord_command):
        with self.__atomic:
            if self.__locked:
                self.__queue.append(_concoord_command)
                raise BlockingReturn()
            else:
                self.__locked = True
                self.__owner = _concoord_command.client

    def release(self, _concoord_command):
        with self.__atomic:
            if self.__owner != _concoord_command.client:
                raise RuntimeError("cannot release un-acquired lock")
            if len(self.__queue) > 0:
                unblockcommand = self.__queue.pop(0)
                self.__owner = unblockcommand.client
                # add the popped command to the exception args
                unblocked = {}
                unblocked[unblockcommand] = True
                raise UnblockingReturn(unblockeddict=unblocked)
            elif len(self.__queue) == 0:
                self.__owner = None
                self.__locked = False

    def __str__(self):
        return "<%s object>" % (self.__class__.__name__)

