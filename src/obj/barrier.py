from threading import Lock
from threadingobj.dcondition import DCondition

class Barrier():
    """Barrier object that supports following functions:
    - create: to reinitialize the object
    - wait: takes a thread who wants to wait on the barrier
    """
    def __init__(self):
        pass

    def create(self, args, **kwargs):
        self.limit = int(args[0])
        self.current = 0
        self.atomic = Lock()
        self.everyoneready = DCondition(self.atomic)

    def wait(self, args, **kwargs):
        print self
        self.everyoneready.acquire(kwargs)
        self.current += 1
        if self.current != self.limit:
            self.everyoneready.wait(kwargs)
        else:
            self.current = 0
            self.everyoneready.notifyAll(kwargs)
        self.everyoneready.release(kwargs)
        
    def __str__(self):
        return "Barrier %d/%d" % (self.current, self.limit)
        
    
        
        
