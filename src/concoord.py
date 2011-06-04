from threading import Lock

from message import Message, PaxosMessage, HandshakeMessage, AckMessage, ClientMessage, UpdateMessage
from connection import Connection, ConnectionPool
from exception import *
from enums import *

RCODE_UNBLOCK, RCODE_BLOCK_UNTIL_NOTICE = range(2)

def return_outofband(designated, owner, command, destinations, retval):
    for dest in destinations:
        clientreply = ClientMessage(MSG_CLIENTMETAREPLY, owner.me, retval, command.clientcommandnumber)
        destconn = owner.clientpool.get_connection_by_peer(dest)
        if destconn.thesocket == None:
            return
        destconn.send(clientreply)

class DistributedLock():
    def __init__(self):
        self.locked = False
        self.holder = None
        self.queue = []
    
    def acquire(self, _concoord_designated, _concoord_owner, _concoord_command):
        if self.locked == True:
            return_outofband(_concoord_designated, _concoord_owner, _concoord_command, [_concoord_command.client], RCODE_BLOCK_UNTIL_NOTICE)
            raise UnusualReturn
        else:
            self.locked = True
            self.queue.append(_concoord_command.client)
            return True

    def release(self, _concoord_designated, _concoord_owner, _concoord_command):
        if self.locked == True and self.holder == _concoord_command.client:
            if len(self.queue) == 0:
                self.holder = None
                self.locked = False
            else:
                self.holder = self.queue.pop()
            return_outofband(_concoord_designated, _concoord_owner, _concoord_command, [_concoord_command.client], RCODE_UNBLOCK)
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
        self.members = []
    
    def acquire(self):
        if self.locked == True:
            return_outofband(_concoord_me, _concoord_client_cmdno, caller, RCODE_BLOCK_UNTIL_NOTICE)
            raise UnusualReturn
        else:
            pass

    def release(self):
        return_outofband(_concoord_me, _concoord_client_cmdno, caller, RCODE_UNBLOCK)
        raise concoord.UnusualReturn

    def wait(self):
        self.members.append(caller)
        return_outofband(_concoord_me, _concoord_client_cmdno, caller, RCODE_BLOCK_UNTIL_NOTICE)
        raise UnusualReturn

    def notify(self):
        return_outofband(_concoord_me, _concoord_client_cmdno, self.members.pop(), RCODE_UNBLOCK)
        raise UnusualReturn

    def notifyAll(self):
        return_outofband(_concoord_me, _concoord_client_cmdno, self.members, RCODE_UNBLOCK)
        raise UnusualReturn

    def __str__(self):
        return 'Distributed Condition: %s' % (" ".join([str(m) for m in self.members]))
