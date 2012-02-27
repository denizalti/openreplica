"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: RLock Coordination Object
@copyright: See LICENSE
"""
from threading import Lock, error
from concoord.enums import *
from concoord.exception import *

class DRLock():
    def __init__(self):
        self.lockcount = 0
        self.holder = None
        self.queue = []
        self.atomic = Lock()
        
    def acquire(self, kwargs):
        command = kwargs['_concoord_command']
        with self.atomic:
            if self.lockcount > 0 and self.holder != command.client:
                self.queue.append(command)
                raise BlockingReturn()
            elif self.lockcount > 0 and self.holder == command.client:
                self.lockcount += 1                
            else:
                self.lockcount = 1
                self.holder = command.client

    def release(self, kwargs):
        command = kwargs['_concoord_command']
        with self.atomic:
            if self.lockcount > 0:
                self.lockcount -= 1
            else:
                raise RuntimeError("cannot release un-acquired lock")
            
            if self.lockcount == 0 and len(self.queue) > 0:
                self.lockcount += 1
                newcommand = self.queue.pop(0)
                self.holder = newcommand.client
                # add the popped command to the exception args
                unblocked = {}
                unblocked[unblockcommand] = True
                raise UnblockingReturn(unblockeddict=unblocked)
            elif self.lockcount == 0 and len(self.queue) == 0:
                self.holder = None
                self.lockcount = 0
            else:
                pass
                
    def __str__(self):
        return '<concoord.threadingobjects.drlock object>'
    
