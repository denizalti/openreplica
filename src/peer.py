from enums import *
from utils import *
import struct
from connection import *

class Peer():
    def __init__(self,peeraddr,peerport,peertype=-1):
        self.type = peertype
        self.port = peerport
        self.addr = peeraddr

    def id(self):
        return "%s:%d" % (self.addr,self.port)

    def sendWaitReply(self, sendernode, message):
        connection = sendernode.connectionpool.getConnectionToPeer(self)
        connection.send(message)
        if message.type != MSG_BYE:
            return connection.receive()
        else:
            connection.close()
            return None

    def send(self, message):
        connection = Connection(self)
        connection.send(message)
        connection.close()
    
    def __hash__(self):
        return self.id().__hash__()

    def __eq__(self, otherpeer):
        return self.addr == otherpeer.addr and self.port == otherpeer.port
        
    def __str__(self):
        return '%s PEER(%s:%d)' % (node_names[self.type] if self.type != -1 else "UNKNOWN", self.addr, self.port)
