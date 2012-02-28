from threading import Lock
from concoord.threadingobject.dcondition import DCondition

class Barrier():
    """Barrier object that supports following functions:
    - wait: takes a thread who wants to wait on the barrier
    """
    def __init__(self, count=1, **kwargs):
        self.count = int(count)
        self.current = 0
        self.condition = DCondition()

    def wait(self, **kwargs):
        self.condition.acquire(kwargs)
        self.current += 1
        if self.current != self.count:
            self.condition.wait(kwargs)
        else:
            self.current = 0
            self.condition.notifyAll(kwargs)
        self.condition.release(kwargs)
        
    def __str__(self, **kwargs):
        return "<%s object>" % (self.__class__.__name__)
        
    
        
        
