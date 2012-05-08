"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example condition
@copyright: See LICENSE
"""
from concoord.threadingobject.dcondition import DCondition

class Condition():
    """Lock object that supports following functions:
    - acquire: locks the object
    - release: unlocks the object
    """
    def __init__(self, lock=None, **kwargs):
        self.condition = DCondition()

    def __repr__(self, **kwargs):
        return repr(self.condition)

    def acquire(self, **kwargs):
        try:
            self.condition.acquire(kwargs)
        except Exception as e:
            raise e
        
    def release(self, **kwargs):
        try:
            self.condition.release(kwargs)
        except Exception as e:
            raise e
        
    def wait(self, **kwargs):
        try:
            self.condition.wait(kwargs)
        except Exception as e:
            raise e
        
    def notify(self, **kwargs):
        try:
            self.condition.notify(kwargs)
        except Exception as e:
            raise e

    def notifyAll(self, **kwargs):
        try:
            self.condition.notifyAll(kwargs)
        except Exception as e:
            raise e

    def __str__(self, **kwargs):
        return str(self.condition)
