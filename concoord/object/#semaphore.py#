"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example semaphore object
@copyright: See LICENSE
"""
from concoord.threadingobject.dsemaphore import DSemaphore

class Semaphore():
    def __init__(self, count=1):
        self.semaphore = DSemaphore(count)

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
