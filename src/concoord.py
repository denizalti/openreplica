from connection import Connection, ConnectionPool
from threading import Lock

class DistributedCondition():
    def __init__(self, lock=None):
        if lock:
            self.lock = lock
        else:
            self.lock = Lock()
        self.members = []
    
    def acquire(self):
        if self.locked == True:
            concoord.return_outofband(_concoord_me, _concoord_client_cmdno, caller, concoord.RCODE_BLOCK_UNTIL_NOTICE)
            raise concoord.UnusualReturn
        else:
            pass

    def release(self):
        concoord.return_outofband(_concoord_me, _concoord_client_cmdno, caller, concoord.RCODE_UNBLOCK)
        raise concoord.UnusualReturn

    def wait(self):
        self.members.append(caller)
        concoord.return_outofband(_concoord_me, _concoord_client_cmdno, caller, concoord.RCODE_BLOCK_UNTIL_NOTICE)
        raise concoord.UnusualReturn

    def notify(self):
        concoord.return_outofband(_concoord_me, _concoord_client_cmdno, self.members.pop(), concoord.RCODE_UNBLOCK)
        raise concoord.UnusualReturn

    def notifyAll(self):
        concoord.return_outofband(_concoord_me, _concoord_client_cmdno, self.members, concoord.RCODE_UNBLOCK)
        raise concoord.UnusualReturn

    def __str__(self):
        return 'Distributed Condition: %s' % (" ".join([str(m) for m in self.members]))

class DistributedLock():
    def __init__(self):
        self.locked = False
    
    def acquire(self):
        if self.locked == True:
            concoord.return_outofband(_concoord_me, _concoord_client_cmdno, caller, concoord.RCODE_BLOCK_UNTIL_NOTICE)
            raise concoord.UnusualReturn
        else:
            self.locked = True
            return True

    def release(self):
        if self.locked == True:
            concoord.return_outofband(_concoord_me, _concoord_client_cmdno, caller, concoord.RCODE_BLOCK_UNTIL_NOTICE)
            raise concoord.UnusualReturn
        else:
            self.locked = True
            return True

    def __str__(self):
        return 'Distributed Lock: LOCKED' if self.locked else 'Distributed Lock: UNLOCKED'
    
def return_outofband(source, clientcommandnumber, destinations, retval):
    for dest in destinations:
        clientreply = ClientMessage(MSG_CLIENTMETAREPLY, source.me, retval, clientcommandnumber)
        destconn = source.clientpool.get_connection_by_peer(dest)
        if destconn.thesocket == None:
            return
        destconn.send(clientreply)


RCODE_UNBLOCK, RCODE_BLOCK_UNTIL_NOTICE = range(2)
