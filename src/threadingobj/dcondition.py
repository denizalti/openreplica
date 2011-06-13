#from concoord import *
#from exception import *
from threading import RLock
from drlock import RLock
    
class DCondition():
    def __init__(self):
        self.atomic = RLock()
        self.lock = DLock()
        self.__waiters = []
    
    def acquire(self, kwargs):
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        self.lock.acquire()

    def release(self, kwargs):
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        self.lock.release()

    def wait(self, kwargs):
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        # put the caller on waitinglist and take the lock away
        with self.atomic:
            if self.lock.locked == True and self.lock.holder == _concoord_command.client:
                self.__waiters.append(_concoord_command)
                self.lock.release()
            else:
                raise RuntimeError("cannot wait on un-acquired lock")

    def notify(self, kwargs):
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        # Notify the next client on the wait list
        with self.atomic:
            if self.lock.locked == True and self.lock.holder == _concoord_command.client:
                nextcommand = self.queue.pop(0)
                return_outofband(_concoord_designated, _concoord_owner, nextcommand)
            else:
                raise RuntimeError("cannot notify on un-acquired lock")         

    def notifyAll(self, kwargs):
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        # Notify every client on the wait list
        with self.atomic:
            if self.lock.locked == True and self.lock.holder == _concoord_command.client:
                for waitcommand in self.__waiters:
                    return_outofband(_concoord_designated, _concoord_owner, waitcommand)
            else:
                raise RuntimeError("cannot notify on un-acquired lock")   

    def __str__(self, kwargs):
        temp = 'Distributed Condition'
        try:
            temp += "\nlockholder: %s\nlockqueue: %s\nwaiters: %s\n" % (self.lockholder, " ".join([str(l) for l in self.lockqueue]), " ".join([str(w) for w in self.waiting]))
        except:
            pass
        return temp

