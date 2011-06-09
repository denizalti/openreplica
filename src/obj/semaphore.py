from concoord import DistributedLock

class Semaphore():
    """Block object that supports following functions:
    - acquire: locks the object
    - release: unlocks the object
    """
    def __init__(self):
        pass()

    def create(self, args, **kwargs):
        self.count = int(args[0])
        self.queue = []
        self.atomic = Lock()

    def acquire(self, args, **kwargs):
        with self.atomic:
            self.count -= 1
            if self.count < 0:
                self.queue.append(XXX)
                block
        
    def release(self, args, **kwargs):
        with self.atomic:
            self.count += 1
            if self.count < 0:
                self.queue.reverse()
                lockholder = self.queue.pop()
                self.queue.reverse()
                unblock lockholder
    
    def __str__(self):
        return str(self.lock)
