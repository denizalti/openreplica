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
    def __init__(self):
        self.lock = DLock()

    def __repr__(self):
        return repr(self.lock)

    def acquire(self, _concoord_command):
        try:
            return self.lock.acquire(_concoord_command)
        except Exception as e:
            raise e

    def release(self, _concoord_command):
        try:
            self.lock.release(_concoord_command)
        except Exception as e:
            raise e

    def __str__(self):
        return str(self.lock)
