import copy
from threading import Lock
from concoord import DistributedLock, DistributedCondition

class Barrier():
    """Barrier object that supports following functions:
    - wait: takes a thread who wants to wait on the barrier
    """
    def __init__(self):
        pass

    def create(self, number, _concoord_designated, _concoord_owner, _concoord_command):
        self.limit = int(number)
        self.current = 0
        self.atomic = Lock()
        self.everyoneready = DistributedCondition(self.atomic)
        print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

    def wait(self, _concoord_designated, _concoord_owner, _concoord_command):
        with self.atomic:
            self.current += 1
            while self.current != self.limit:
                self.everyoneready.wait(_concoord_designated, _concoord_owner, _concoord_command)
            self.current = 0
            self.everyoneready.notifyall(_concoord_designated, _concoord_owner, _concoord_command)
        
    def __str__(self):
        return "Barrier %d/%d" % (self.current, self.limit)
        
    
        
        
