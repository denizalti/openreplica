import copy
import paxi
from threading import Lock
from cooncoord import DistributedLock, DistributedCondition

class Barrier():
    """Barrier object that supports following functions:
    - wait: takes a thread who wants to wait on the barrier
    """
    def __init__(self, number):
        self.limit = number
        self.current = 0
        self.atomic = Lock()
        self.everyoneready = DistributedCondition(self.atomic)

    def wait(self, **kwargs):
        with self.atomic:
            self.current += 1
            while self.current != self.limit:
                self.everyoneready.wait(kwargs)
            self.current = 0
            self.everyoneready.notifyall()
        
    def __str__(self):
        return "Barrier %d/%d: %s" % (self.current, self.limit, " ".join([str(m) for m in self.members]))
        
    
        
        
