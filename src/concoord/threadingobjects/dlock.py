"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Lock Coordination Object
@copyright: See LICENSE
"""
from threading import Lock, error
from concoord.enums import *
from concoord.exception import *

class DLock():
    def __init__(self):
        self.locked = False
        self.holder = None
        self.queue = []
        self.atomic = Lock()
    
    def acquire(self, _concoord_command):
        with self.atomic:
            if self.locked:
                self.queue.append(_concoord_command)
                raise BlockingReturn(None)
            else:
                self.locked = True          
                self.holder = _concoord_command.client

    def release(self, _concoord_command):
        with self.atomic:
            if self.locked and self.holder == _concoord_command.client:
                if len(self.queue) > 0:
                    newcommand = self.queue.pop(0)
                    self.holder = newcommand.client
                    # add the popped command to the exception args
                    unblocked = {}
                    unblocked[unblockcommand] = True
                    raise UnblockingReturn(None, unblocked)
                elif len(self.queue) == 0:
                    self.holder = None
                    self.locked = False
            else:
                raise error("release unlocked lock")
                
    def __str__(self):
        return "Distributed Lock\nholder: %s\nqueue: %s\n" % (self.holder, " ".join([str(m) for m in self.queue]))
