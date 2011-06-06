from threading import Lock

from message import Message, PaxosMessage, HandshakeMessage, AckMessage, ClientMessage, ClientReplyMessage, UpdateMessage
from connection import Connection, ConnectionPool
from exception import *
from enums import *

def return_outofband(designated, owner, command):
    clientreply = ClientReplyMessage(MSG_CLIENTMETAREPLY, owner.me, replycode=CR_METAREPLY, inresponseto=command.clientcommandnumber)
    destconn = owner.clientpool.get_connection_by_peer(command.client)
    if destconn.thesocket == None:
        return
    destconn.send(clientreply)

class DistributedLock():
    def __init__(self):
        self.locked = False
        self.holder = None
        self.queue = []
        self.lock = Lock()
    
    def acquire(self, _concoord_designated, _concoord_owner, _concoord_command):
        if self.locked == True:
            self.queue.append(_concoord_command)
            raise UnusualReturn
        else:
            self.holder = _concoord_command.client
            self.locked = True

    def release(self, _concoord_designated, _concoord_owner, _concoord_command):
        if self.locked == True and self.holder == _concoord_command.client:
            with self.lock:
                if len(self.queue) == 0:
                    self.holder = None
                    self.locked = False
                else:
                    self.queue.reverse()
                    newcommand = self.queue.pop()
                    self.queue.reverse()
                    self.holder = newcommand.client
                    # return to old holder which made a release
                    return_outofband(_concoord_designated, _concoord_owner, _concoord_command)
                    # return to new holder which is waiting
                    return_outofband(_concoord_designated, _concoord_owner, newcommand)
                    raise UnusualReturn
        else:
            return "Release on unacquired lock"

    def __str__(self):
        return 'Distributed Lock: LOCKED' if self.locked else 'Distributed Lock: UNLOCKED'
    
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
    
    def acquire(self, _concoord_designated, _concoord_owner, _concoord_command):
        if self.locked == True:
            self.lockqueue.append(_concoord_command)
            raise UnusualReturn
        else:
            self.lockholder = _concoord_command.client
            self.locked = True

    def release(self, _concoord_designated, _concoord_owner, _concoord_command):
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
                    # return to old holder which made a release
                    return_outofband(_concoord_designated, _concoord_owner, _concoord_command)
                    # return to new holder which is waiting
                    return_outofband(_concoord_designated, _concoord_owner, newcommand)
                    raise UnusualReturn
        else:
            return "Release on unacquired lock"

    def wait(self, _concoord_designated, _concoord_owner, _concoord_command):
        # put the caller on waitinglist and take the lock away
        self.waiting.append(caller)
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
                    # return to old holder which made a release
                    return_outofband(_concoord_designated, _concoord_owner, _concoord_command)
                    # return to new holder which is waiting
                    return_outofband(_concoord_designated, _concoord_owner, newcommand)
                    raise UnusualReturn
        else:
            return "Can't wait on unacquired condition"
        

    def notify(self):
        self.waiting.reverse()
        nextcommand = self.queue.pop()
        self.waiting.reverse()
        return_outofband(_concoord_designated, _concoord_owner, nextcommand, [nextcommand.client])
        raise UnusualReturn

    def notifyAll(self):
        # the command thing needs fixing
        #return_outofband(_concoord_designated, _concoord_owner, nextcommand, [self.waiting])
        raise UnusualReturn

    def __str__(self):
        return 'Distributed Condition: %s' % (" ".join([str(m) for m in self.waiting]))
