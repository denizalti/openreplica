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
        # _paxi_designated, _paxi_client_cmdno, _paxi_me
        if self.locked == True:
            paxi.return_outofband(_paxi_me, _paxi_client_cmdno, caller, paxi.RCODE_BLOCK_UNTIL_NOTICE)
            raise paxi.UnusualReturn
        else:
            pass

    def release(self):
        # _paxi_designated, _paxi_client_cmdno, _paxi_me
        paxi.return_outofband(_paxi_me, _paxi_client_cmdno, caller, paxi.RCODE_UNBLOCK)
        raise paxi.UnusualReturn

    def wait(self):
        # _paxi_designated, _paxi_client_cmdno, _paxi_me
        self.members.append(caller)
        paxi.return_outofband(_paxi_me, _paxi_client_cmdno, caller, paxi.RCODE_BLOCK_UNTIL_NOTICE)
        raise paxi.UnusualReturn

    def notify(self):
        # _paxi_designated, _paxi_client_cmdno, _paxi_me
        paxi.return_outofband(_paxi_me, _paxi_client_cmdno, self.members.pop(), paxi.RCODE_UNBLOCK)
        raise paxi.UnusualReturn

    def notifyAll(self):
        # _paxi_designated, _paxi_client_cmdno, _paxi_me
        paxi.return_outofband(_paxi_me, _paxi_client_cmdno, self.members, paxi.RCODE_UNBLOCK)
        raise paxi.UnusualReturn

    def __str__(self):
        pass

class DistributedLock():
    def __init__(self):
        self.locked = False
    
    def acquire(self):
        # _paxi_designated, _paxi_client_cmdno, _paxi_me
        if self.locked == True:
            paxi.return_outofband(_paxi_me, _paxi_client_cmdno, caller, concoord.RCODE_BLOCK_UNTIL_NOTICE)
            raise paxi.UnusualReturn
        else:
            self.locked = True
            return True

    def release(self):
        # _paxi_designated, _paxi_client_cmdno, _paxi_me
        if self.locked == True:
            paxi.return_outofband(_paxi_me, _paxi_client_cmdno, caller, concoord.RCODE_BLOCK_UNTIL_NOTICE)
            raise paxi.UnusualReturn
        else:
            self.locked = True
            return True

    def __str__(self):
        pass

def return_outofband(source, clientcommandnumber, destinations, retval):
    for dest in destinations:
        clientreply = ClientMessage(MSG_CLIENTMETAREPLY, source.me, retval, clientcommandnumber)
        destconn = source.clientpool.get_connection_by_peer(dest)
        if destconn.thesocket == None:
            return
        destconn.send(clientreply)


RCODE_UNBLOCK, RCODE_BLOCK_UNTIL_NOTICE = range(2)
