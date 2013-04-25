"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example rlock object
@copyright: See LICENSE
"""
from concoord.threadingobject.drlock import DRLock

class RLock():
    def __init__(self):
        self.rlock = DRLock()

    def __repr__(self):
        return repr(self.rlock)

    def acquire(self, _concoord_command):
        try:
            return self.rlock.acquire(_concoord_command)
        except Exception as e:
            raise e

    def release(self, _concoord_command):
        try:
            self.rlock.release(_concoord_command)
        except Exception as e:
            raise e

    def __str__(self):
        return str(self.rlock)
