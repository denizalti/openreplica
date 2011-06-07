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
    def __init__(self):
        self.locked = False
        self.holder = None
        self.queue = []
        self.lock = Lock()
    
    def acquire(self, kwargs):
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        if self.locked == True:
            self.queue.append(_concoord_command)
            raise UnusualReturn
        else:
            self.holder = _concoord_command.client
            self.locked = True

    def release(self, kwargs):
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
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
        print "Distributed Condition INIT!"
        if lock:
            self.lock = lock
        else:
            self.lock = Lock()
        self.locked = False
        self.lockholder = None
        self.lockqueue = []
        self.waiting = []
    
    def acquire(self, kwargs):
        print "Distributed Condition ACQUIRE!"
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        if self.locked == True:
            self.lockqueue.append(_concoord_command)
            raise UnusualReturn
        else:
            self.lockholder = _concoord_command.client
            self.locked = True

    def release(self, kwargs):
        print "Distributed Condition RELEASE!"
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
                    # return to old holder which made a release
                    return_outofband(_concoord_designated, _concoord_owner, _concoord_command)
                    # return to new holder which is waiting
                    return_outofband(_concoord_designated, _concoord_owner, newcommand)
                    raise UnusualReturn
        else:
            return "Release on unacquired lock"

    def wait(self, kwargs):
        print "Distributed Condition WAIT!"
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        # put the caller on waitinglist and take the lock away
        if self.locked == True and self.lockholder == _concoord_command.client:
            with self.lock:
                print "Peki"
                self.waiting.append(_concoord_command)
                if len(self.lockqueue) == 0:
                    print "Noluyo"
                    self.lockholder = None
                    self.locked = False
                else:
                    print "Anlamadim"
                    self.lockqueue.reverse()
                    newcommand = self.lockqueue.pop()
                    self.lockqueue.reverse()
                    self.lockholder = newcommand.client
                    # return to old holder which made a release
                    return_outofband(_concoord_designated, _concoord_owner, _concoord_command)
                    # return to new holder which is waiting
                    return_outofband(_concoord_designated, _concoord_owner, newcommand)
                print "HEEEEEEEEEEEEEEEHEHEHE"
                raise UnusualReturn
        else:
            return "Can't wait on unacquired condition"
        

    def notify(self, kwargs):
        print "Distributed Condition NOTIFY!"
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        # Notify the next client on the wait list
        with self.lock:
            self.waiting.reverse()
            nextcommand = self.queue.pop()
            self.waiting.reverse()
        return_outofband(_concoord_designated, _concoord_owner, nextcommand)
        raise UnusualReturn

    def notifyAll(self, kwargs):
        print "Distributed Condition NOTIFYALL!"
        _concoord_designated, _concoord_owner, _concoord_command = kwargs['_concoord_designated'], kwargs['_concoord_owner'], kwargs['_concoord_command']
        # Notify every client on the wait list
        with self.lock:
            self.waiting.reverse()
            for client in self.waiting:
                nextcommand = self.waiting.pop()
                return_outofband(_concoord_designated, _concoord_owner, nextcommand)
        raise UnusualReturn

    def __str__(self, kwargs):
        return 'Distributed Condition: %s' % (" ".join([str(m) for m in self.waiting]))
