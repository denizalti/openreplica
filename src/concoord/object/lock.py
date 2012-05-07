"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example lock
@copyright: See LICENSE
"""
from concoord.threadingobject.dlock import DLock

class Lock():
    """Lock object that supports following functions:
    - acquire: locks the object
    - release: unlocks the object
    """
    def __init__(self, **kwargs):
        self.lock = DLock()

    def __repr__(self, **kwargs):
        return repr(self.lock)

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
