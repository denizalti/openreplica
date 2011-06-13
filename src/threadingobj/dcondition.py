#from concoord import *
from returns import *
from exception import *
from threading import RLock
from drlock import DRLock
from dlock import DLock
    
class DCondition():
    def __init__(self):
        self.atomic = RLock()
        self.lock = DLock()
        self.__waiters = []
    
    def acquire(self, kwargs):
        try:
            return self.lock.acquire(kwargs)
        except UnusualReturn:
            raise UnusualReturn

    def release(self, kwargs):
#        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        return self.lock.release(kwargs)

    def wait(self, kwargs):
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        # put the caller on waitinglist and take the lock away
        with self.atomic:
            if self.lock.locked == True and self.lock.holder == _concoord_command.client:
                self.__waiters.append(_concoord_command)
                self.lock.release(kwargs)
                raise UnusualReturn
            else:
                raise RuntimeError("cannot wait on un-acquired lock")

    def notify(self, kwargs):
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        # Notify the next client on the wait list
        with self.atomic:
            if self.lock.locked == True and self.lock.holder == _concoord_command.client:
                waitcommand = self.__waiters.pop(0)
                return_outofband(_concoord_designated, _concoord_owner, waitcommand)
                # Upon notifying the client continues *without* the lock! I have to make a trick for this.
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

    def __str__(self):
        temp = 'Distributed Condition'
        #try:
        temp += "\nlock: %s\nwaiters: %s\n" % (str(self.lock), " ".join([str(w) for w in self.__waiters]))
        #except:
        #    pass
        return temp

