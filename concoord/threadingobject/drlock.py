"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: RLock Coordination Object
@copyright: See LICENSE
"""
from threading import Lock
from concoord.enums import *
from concoord.exception import *

class DRLock():
    def __init__(self):
        self.__count = 0
        self.__owner = None
        self.__queue = []
        self.__atomic = Lock()

    def __repr__(self):
        return "<%s owner=%r count=%d>" % (self.__class__.__name__, self.__owner, self.__count)

    def acquire(self, _concoord_command):
        with self.__atomic:
            if self.__count > 0 and self.__owner != _concoord_command.client:
                self.__queue.append(_concoord_command)
                raise BlockingReturn()
            elif self.__count > 0 and self.__owner == _concoord_command.client:
                self.__count += 1
                return 1
            else:
                self.__count = 1
                self.__owner = _concoord_command.client
                return True

    def release(self, _concoord_command):
        with self.__atomic:
            if self.__owner != _concoord_command.client:
                raise RuntimeError("cannot release un-acquired lock")
            self.__count -= 1

            if self.__count == 0 and len(self.__queue) > 0:
                self.__count += 1
                unblockcommand = self.__queue.pop(0)
                self.__owner = unblockcommand.client
                # add the popped command to the exception args
                unblocked = {}
                unblocked[unblockcommand] = True
                raise UnblockingReturn(unblockeddict=unblocked)
            elif self.__count == 0 and len(self.__queue) == 0:
                self.__owner = None

    # Internal methods used by condition variables
    def _is_owned(self, client):
        return self.__owner == client

    def _add_to_queue(self, clientcommand):
        self.__queue.append(clientcommand)

    def __str__(self):
        return "<%s object>" % (self.__class__.__name__)

