"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example boundedsemaphore object
@copyright: See LICENSE
"""
from concoord.threadingobjects.dboundedsemaphore import DBoundedSemaphore

class BoundedSemaphore():
    """Semaphore object that supports following functions:
    - acquire: locks the object
    - release: unlocks the object
    """
    def __init__(self, count=1, **kwargs):
        self.semaphore = DBoundedSemaphore(count)
            
    def acquire(self, **kwargs):
        try:
            return self.semaphore.acquire(kwargs)
        except Exception as e:
            raise e
        
    def release(self, **kwargs):
        try:
            return self.semaphore.release(kwargs)
        except Exception as e:
            raise e
    
    def __str__(self, **kwargs):
        return str(self.semaphore)
