from threading import Lock
from concoord.exception import *

class DBoundedSemaphore():
    def __init__(self, count=1):
        self.limit = int(count)
        self.count = int(count)
        self.queue = []
        self.atomic = Lock()

    def create(self, count=1):
        self.limit = int(count)
        self.count = int(count)
        self.queue = []
    
    def acquire(self, kwargs):
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        with self.atomic:
            self.count -= 1
            if self.count < 0:
                self.queue.append(_concoord_command)
                raise UnusualReturn

    def release(self, kwargs):
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        with self.atomic:
            if self.count == self.limit:
                return ValueError("Semaphore bound exceeded")
            else:
                self.count += 1
            if len(self.queue) > 0:
                newcommand = self.queue.pop(0)
                # return to new holder which is waiting
                return_outofband(_concoord_designated, _concoord_owner, newcommand)
                
    def __str__(self):
        return "Distributed BoundedSemaphore\ncount: %d\nqueue: %s\n" % (self.count, " ".join([str(m) for m in self.queue]))
