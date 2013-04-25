"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example condition
@copyright: See LICENSE
"""
from concoord.threadingobject.dcondition import DCondition

class Condition():
    def __init__(self, lock=None):
        self.condition = DCondition()

    def __repr__(self):
        return repr(self.condition)

    def acquire(self, _concoord_command):
        try:
            self.condition.acquire(_concoord_command)
        except Exception as e:
            raise e

    def release(self, _concoord_command):
        try:
            self.condition.release(_concoord_command)
        except Exception as e:
            raise e

    def wait(self, _concoord_command):
        try:
            self.condition.wait(_concoord_command)
        except Exception as e:
            raise e

    def notify(self, _concoord_command):
        try:
            self.condition.notify(_concoord_command)
        except Exception as e:
            raise e

    def notifyAll(self, _concoord_command):
        try:
            self.condition.notifyAll(_concoord_command)
        except Exception as e:
            raise e

    def __str__(self):
        return str(self.condition)
