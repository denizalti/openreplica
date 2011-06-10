from threading import Lock
from concoord import DistributedLock

class Semaphore():
    """Block object that supports following functions:
    - acquire: locks the object
    - release: unlocks the object
    """
    def __init__(self):
        pass

    def create(self, args, **kwargs):
        self.count = int(args[0])
        self.queue = []
        self.atomic = Lock()
        self.lock = DistributedLock()

    def acquire(self, args, **kwargs):
        with self.atomic:
            self.count -= 1
            if self.count < 0:
                self.lock.acquire(kwargs)
        
    def release(self, args, **kwargs):
        with self.atomic:
            self.count += 1
            if self.count < 0:
                self.lock.release(kwargs)
    
    def __str__(self):
        temp = "Semaphore"
        try:
            temp += "\n count: %d\n queue: %s\n" % (self.count, " ".join([str(m) for m in self.queue]))
        except:
            pass
        return temp
