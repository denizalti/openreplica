from concoord.threadingobjects.dlock import DLock

class Lock():
    """Lock object that supports following functions:
    - acquire: locks the object
    - release: unlocks the object
    """
    def __init__(self, **kwargs):
        self.lock = DLock()

    def acquire(self, **kwargs):
        try:
            return self.lock.acquire(kwargs)
        except Exception as e:
            raise e
        
    def release(self, **kwargs):
        try:
            self.lock.release(kwargs)
        except Exception as e:
            raise e
    
    def __str__(self, **kwargs):
        return str(self.lock)
