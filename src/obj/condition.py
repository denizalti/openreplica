from threadingobj.dcondition import DCondition

class Lock():
    """Lock object that supports following functions:
    - acquire: locks the object
    - release: unlocks the object
    """
    def __init__(self):
        self.condition = DCondition()

    def acquire(self, args, **kwargs):
        self.condition.acquire(kwargs)
        
    def release(self, args, **kwargs):
        self.condition.release(kwargs)

    def wait(self, args, **kwargs):
        self.condition.acquire(kwargs)

    def notify(self, args, **kwargs):
        self.condition.acquire(kwargs)

    def notifyAll(self, args, **kwargs):
        self.condition.acquire(kwargs)

    def __str__(self):
        return str(self.lock)
