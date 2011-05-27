from cooncoord import DistributedLock

class Lock():
    """Block object that supports following functions:
    - acquire: locks the object
    - release: unlocks the object
    """
    def __init__(self):
        self.lock = DistributedLock()

    def acquire(self, **kwargs):
        self.lock.acquire()
        
    def release(self, **kwargs):
        self.lock.release()
    
    def __str__(self):
        return str(self.lock
        
    
        
        
