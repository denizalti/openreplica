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
    def __init__(self, lock=None):
        self.condition = DCondition()

    def __repr__(self):
        return repr(self.condition)

    def acquire(self):
        try:
            self.condition.acquire(_concoord_command)
        except Exception as e:
            raise e
        
    def release(self):
        try:
            self.condition.release(_concoord_command)
        except Exception as e:
            raise e
        
    def wait(self):
        try:
            self.condition.wait(_concoord_command)
        except Exception as e:
            raise e
        
    def notify(self):
        try:
            self.condition.notify(_concoord_command)
        except Exception as e:
            raise e

    def notifyAll(self):
        try:
            self.condition.notifyAll(_concoord_command)
        except Exception as e:
            raise e

    def __str__(self):
        return str(self.condition)
