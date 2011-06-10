from threading import Lock

from message import Message, PaxosMessage, HandshakeMessage, AckMessage, ClientMessage, ClientReplyMessage, UpdateMessage
from connection import Connection, ConnectionPool
from exception import *
from enums import *

def return_outofband(designated, owner, command):
    if not designated:
        return
    clientreply = ClientReplyMessage(MSG_CLIENTMETAREPLY, owner.me, replycode=CR_METAREPLY, inresponseto=command.clientcommandnumber)
    destconn = owner.clientpool.get_connection_by_peer(command.client)
    if destconn.thesocket == None:
        return
    destconn.send(clientreply)

class DistributedLock():
    def __init__(self, count=1):
        self.count = int(count)
        self.holder = None
        self.queue = []
        self.atomic = Lock()
    
    def acquire(self, kwargs):
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        with self.atomic:
            self.count -= 1
            if self.count < 0:
                self.queue.append(_concoord_command)
                raise UnusualReturn
            else:
                self.holder = _concoord_command.client

    def release(self, kwargs):
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        with self.atomic:
            self.count += 1
            if len(self.queue) > 0:
                self.queue.reverse()
                newcommand = self.queue.pop()
                self.queue.reverse()
                self.holder = newcommand.client
                # return to new holder which is waiting
                return_outofband(_concoord_designated, _concoord_owner, newcommand)
            elif len(self.queue) == 0:
                self.holder = None
                self.locked = False
                
    def __str__(self):
        temp = 'Distributed Lock' if self.count == 1 else 'Distributed Semaphore'
        temp += "\ncount: %d\nholder: %s\nqueue: %s\n" % (self.count, self.holder, " ".join([str(m) for m in self.queue]))
        return temp
    
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
