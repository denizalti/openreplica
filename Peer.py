from Utils import *
import struct
import Connection
from Message import *

class Peer():
    def __init__(self,id,addr,port,type):
        self.port = port
        self.addr = addr
        self.id = id
        self.type = type

    def serialize(self):
        return (self.id,self.addr,self.port,self.type)
    
    def pack(self):
        return struct.pack("I%dsII" % ADDRLENGTH, self.id,self.addr,self.port,self.type)
    
    def send(self, message):
        reply = ""
        print "Trying to send a message to %s:%d" % (self.addr,self.port)
        connection = Connection.Connection(self.addr,self.port)
        connection.send(message)
        if message.type != MSG_BYE:
            reply = connection.receive()
        connection.close()
        return reply
    
    def __eq__(self, otherpeer):
        if self.id == otherpeer.id:
            if self.addr == otherpeer.addr:
                if self.port == otherpeer.port:
                    return True
        return False
        
    def __str__(self):
        if self.type == LEADER:
            temp = "LEADER "
        elif self.type == ACCEPTOR:
            temp = "ACCEPTOR "
        else:
            temp = "REPLICA "
        temp += 'PEER(%d, %s, %d)' % (self.id, self.addr, self.port)
        return temp
    

    
        
        
