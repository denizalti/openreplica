from concoord import DistributedLock

class Lock():
    """Lock object that supports following functions:
    - acquire: locks the object
    - release: unlocks the object
    """
    def __init__(self):
        self.lock = DistributedLock()

    def acquire(self, args, **kwargs):
        self.lock.acquire(kwargs)
        
    def release(self, args, **kwargs):
        self.lock.release(kwargs)
    
    def __str__(self):
        return str(self.lock)
