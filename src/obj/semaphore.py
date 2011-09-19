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
        if len(args) > 0:
            self.semaphore = DSemaphore(args[0])
        else:
            self.semaphore = DSemaphore()
            
    def acquire(self, args, **kwargs):
        try:
            return self.semaphore.acquire(kwargs)
        except Exception as e:
            raise e
        
    def release(self, args, **kwargs):
        try:
            return self.semaphore.release(kwargs)
        except Exception as e:
            raise e
    
    def __str__(self):
        return str(self.semaphore)
