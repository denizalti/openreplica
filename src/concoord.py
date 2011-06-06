from threading import Lock

from message import Message, PaxosMessage, HandshakeMessage, AckMessage, ClientMessage, ClientReplyMessage, UpdateMessage
from connection import Connection, ConnectionPool
from exception import *
from enums import *

def return_outofband(designated, owner, command, destinations):
    for dest in destinations:
        clientreply = ClientReplyMessage(MSG_CLIENTMETAREPLY, owner.me, replycode=CR_METAREPLY, inresponseto=command.clientcommandnumber)
        destconn = owner.clientpool.get_connection_by_peer(dest)
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
                    oldholder = self.holder
                    self.queue.reverse()
                    newcommand = self.queue.pop()
                    self.holder = newcommand.client
                    self.queue.reverse()
                    # return to old holder which made a release
                    return_outofband(_concoord_designated, _concoord_owner, _concoord_command, [oldholder])
                    # return to new holder which is waiting
                    return_outofband(_concoord_designated, _concoord_owner, newcommand, [self.holder])
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
