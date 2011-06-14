from threadingobj.drlock import DRlock

class Rlock():
    """RLock object that supports following functions:
    - acquire: locks the object
    - release: unlocks the object
    """
    def __init__(self):
        self.lock = DRLock()

    def acquire(self, args, **kwargs):
        self.lock.acquire(kwargs)
        
    def release(self, args, **kwargs):
        self.lock.release(kwargs)
    
    def __str__(self):
        return str(self.lock)
