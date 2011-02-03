from utils import *
import struct
from connection import *

class Peer():
    def __init__(self,peerid,peeraddr,peerport,peertype=-1):
        self.port = peerport
        self.addr = peeraddr
        self.id = peerid
        self.type = peertype

    def serialize(self):
        return (self.id,self.addr,self.port,self.type)
    
    def pack(self):
        return struct.pack("I%dsII" % ADDRLENGTH, self.id,self.addr,self.port,self.type)
    
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
        if self.id == otherpeer.id:
            if self.addr == otherpeer.addr:
                if self.port == otherpeer.port:
                    return True
        return False
        
    def __str__(self):
        temp = '%s PEER(%d, %s, %d)' % (nodeTypes[self.type],self.id, self.addr, self.port)
        return temp
    

    
        
        
