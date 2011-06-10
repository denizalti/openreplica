from concoord import DistributedLock

class Semaphore():
    """Semaphore object that supports following functions:
    - acquire: locks the object
    - release: unlocks the object
    """
    def __init__(self):
        # automatically created with count 1
        self.lock = DistributedLock()

    def create(self, args, **kwargs):
        count = args[0]
        self.lock = DistributedLock(count)

    def acquire(self, args, **kwargs):
        self.lock.acquire(kwargs)
        
    def release(self, args, **kwargs):
        self.lock.release(kwargs)
    
    def __str__(self):
        return str(self.lock)
