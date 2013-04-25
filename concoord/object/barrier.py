"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example barrier object
@copyright: See LICENSE
"""
from threading import Lock
from concoord.threadingobject.dcondition import DCondition

class Barrier():
    def __init__(self, count=1):
        self.count = int(count)
        self.current = 0
        self.condition = DCondition()

    def wait(self, _concoord_command):
        self.condition.acquire(_concoord_command)
        self.current += 1
        if self.current != self.count:
            self.condition.wait(_concoord_command)
        else:
            self.current = 0
            self.condition.notifyAll(_concoord_command)
        self.condition.release(_concoord_command)

    def __str__(self):
        return "<%s object>" % (self.__class__.__name__)




