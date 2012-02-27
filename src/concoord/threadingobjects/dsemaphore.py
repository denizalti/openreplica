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
        self.count = int(count)
        self.queue = []
        self.atomic = Lock()
    
    def acquire(self, kwargs):
        with self.atomic:
            self.count -= 1
            if self.count < 0:
                self.queue.append(kwargs['_concoord_command'])
                raise BlockingReturn()
            else:
                return True

    def release(self, kwargs):
        with self.atomic:
            self.count += 1
            if len(self.queue) > 0:
                unblockcommand = self.queue.pop(0)
                # add the popped command to the exception args
                unblocked = {}
                unblocked[unblockcommand] = True
                raise UnblockingReturn(unblockeddict=unblocked)
                
    def __str__(self):
        return "Distributed Semaphore\ncount: %d\nqueue: %s\n" % (self.count, " ".join([str(m) for m in self.queue]))
