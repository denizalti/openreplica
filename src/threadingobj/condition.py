from concoord import *
from exception import *
    
class DistributedCondition():
    def __init__(self, lock=None):
        if lock:
            self.lock = lock
        else:
            self.lock = Lock()
        self.locked = False
        self.lockholder = None
        self.lockqueue = []
        self.waiting = []
    
    def acquire(self, kwargs):
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        if self.locked == True:
            self.lockqueue.append(_concoord_command)
            raise UnusualReturn
        else:
            self.lockholder = _concoord_command.client
            self.locked = True

    def release(self, kwargs):
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        if self.locked == True and self.holder == _concoord_command.client:
            with self.lock:
                if len(self.lockqueue) == 0:
                    self.lockholder = None
                    self.locked = False
                else:
                    self.lockqueue.reverse()
                    newcommand = self.lockqueue.pop()
                    self.lockqueue.reverse()
                    self.lockholder = newcommand.client
                    # return to new holder which is waiting
                    return_outofband(_concoord_designated, _concoord_owner, newcommand)
        else:
            return "Release on unacquired lock"

    def wait(self, kwargs):
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        # put the caller on waitinglist and take the lock away
        if self.locked == True and self.lockholder == _concoord_command.client:
            with self.lock:
                self.waiting.append(_concoord_command)
                if len(self.lockqueue) == 0:
                    self.lockholder = None
                    self.locked = False
                else:
                    self.lockqueue.reverse()
                    newcommand = self.lockqueue.pop()
                    self.lockqueue.reverse()
                    self.lockholder = newcommand.client
                    # return to new holder which is waiting
                    return_outofband(_concoord_designated, _concoord_owner, newcommand)
                raise UnusualReturn
        else:
            return "Can't wait on unacquired condition"

    def notify(self, kwargs):
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        # Notify the next client on the wait list
        with self.lock:
            self.waiting.reverse()
            nextcommand = self.queue.pop()
            self.waiting.reverse()
        return_outofband(_concoord_designated, _concoord_owner, nextcommand)

    def notifyAll(self, kwargs):
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        # Notify every client on the wait list
        with self.lock:
            self.waiting.reverse()
            for client in self.waiting:
                nextcommand = self.waiting.pop()
                return_outofband(_concoord_designated, _concoord_owner, nextcommand)

    def __str__(self, kwargs):
        temp = 'Distributed Condition: LOCKED' if self.locked else 'Distributed Lock: UNLOCKED'
        try:
            temp += "\nlockholder: %s\nlockqueue: %s\nwaiting: %s\n" % (self.lockholder, " ".join([str(l) for l in self.lockqueue]), " ".join([str(w) for w in self.waiting]))
        except:
            pass
        return temp

