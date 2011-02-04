from enums import *
from utils import *
import struct
from connection import *

class Peer():
    def __init__(self,peeraddr='',peerport=0,peertype=-1):
        self.port = peerport
        self.addr = peeraddr
        self.type = peertype

    def serialize(self):
        return (self.addr,self.port,self.type)

    #XXX: Will change
    def pack(self):
        return struct.pack("I%dsII" % ADDRLENGTH,self.addr,self.port,self.type)
    
    def sendWaitReply(self, message):
        serializedreply = ""
        connection = Connection(self.addr,self.port)
        connection.send(message)
        if message.type != MSG_BYE:
            serializedreply = connection.receive()
        connection.close()
        return serializedreply
    
    def send(self, message):
        connection = Connection(self.addr,self.port)
        connection.send(message)
        connection.close()
    
    def __eq__(self, otherpeer):
            if self.addr == otherpeer.addr:
                if self.port == otherpeer.port:
                    return True
        return False
        
    def __str__(self):
        return '%s [%s:%d]' % (node_names[self.type], self.addr, self.port)
    

    
        
        
