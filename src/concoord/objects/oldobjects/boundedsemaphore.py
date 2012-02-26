from threadingobj.dboundedsemaphore import DBoundedSemaphore

class Boundedsemaphore():
    """Semaphore object that supports following functions:
    - create: to reinitialize the semaphore
    - acquire: locks the object
    - release: unlocks the object
    """
    def __init__(self):
        # automatically created with count 1
        self.semaphore = DBoundedSemaphore()

    def create(self, args, **kwargs):
        count = args[0]
        self.semaphore = DBoundedSemaphore(count)

    def acquire(self, args, **kwargs):
        self.semaphore.acquire(kwargs)
        
    def release(self, args, **kwargs):
        self.semaphore.release(kwargs)
    
    def __str__(self):
        return str(self.semaphore)
