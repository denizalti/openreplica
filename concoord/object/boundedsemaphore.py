"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example boundedsemaphore object
@copyright: See LICENSE
"""
from concoord.threadingobject.dboundedsemaphore import DBoundedSemaphore

class BoundedSemaphore():
    """Semaphore object that supports following functions:
    - acquire: locks the object
    - release: unlocks the object
    """
    def __init__(self, count=1):
        self.semaphore = DBoundedSemaphore(count)

    def __repr__(self):
        return repr(self.semaphore)

    def acquire(self, _concoord_command):
        try:
            return self.semaphore.acquire(_concoord_command)
        except Exception as e:
            raise e

    def release(self, _concoord_command):
        try:
            return self.semaphore.release(_concoord_command)
        except Exception as e:
            raise e

    def __str__(self):
        return str(self.semaphore)
