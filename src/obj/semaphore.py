from threadingobj.dsemaphore import DSemaphore

class Semaphore():
    """Semaphore object that supports following functions:
    - acquire: locks the object
    - release: unlocks the object
    """
    def __init__(self):
        # automatically created with count 1
        self.semaphore = DSemaphore()

    def create(self, args, **kwargs):
        count = args[0]
        self.semaphore = DSemaphore(count)

    def acquire(self, args, **kwargs):
        self.semaphore.acquire(kwargs)
        
    def release(self, args, **kwargs):
        self.semaphore.release(kwargs)
    
    def __str__(self):
        return str(self.semaphore)
