"""
@author: denizalti
@note: Peer
@date: February 1, 2011
"""

from enums import *
from utils import *
import struct
from connection import *

class Peer():
    """Peer instance of a Node"""
    def __init__(self,peeraddr,peerport,peertype=-1):
        """Initialize Peer

        Peer State
        - type: type of Peer (NODE_LEADER | NODE_ACCEPTOR | NODE_REPLICA)
        - port: port of Peer
        - addr: hostname of Peer
        """
        self.type = peertype
        self.port = peerport
        self.addr = peeraddr

    def id(self):
        """Returns the id (addr:port) of the Peer"""
        return "%s:%d" % (self.addr,self.port)

    def sendWaitReply(self, sendernode, message):
        """Sends a given message to Peer and waits for a reply.
        The reply is returned.
        """
        connection = sendernode.connectionpool.getConnectionToPeer(self)
        connection.send(message)
        if message.type == MSG_BYE:
            connection.close()
            return None
        return connection.receive()

    def send(self, sendernode, message):
        """Sends a given message to Peer"""
        connection = sendernode.connectionpool.getConnectionToPeer(self)
        connection.send(message)
    
    def __hash__(self):
        """Returns the hashed id"""
        return self.id().__hash__()

    def __eq__(self, otherpeer):
        """Equality function for two Peers.
        Returns True if given Peer is equal to Peer, False otherwise.
        """
        return self.addr == otherpeer.addr and self.port == otherpeer.port
        
    def __str__(self):
        """Return Peer information"""
        return '%s PEER(%s:%d)' % (node_names[self.type] if self.type != -1 else "UNKNOWN", self.addr, self.port)
