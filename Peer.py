from Utils import *
import struct

class Peer():
    def __init__(self,id,addr,port):
        self.port = port
        self.addr = addr
        self.id = id

    def serialize(self):
        return (self.id,self.addr,self.port)
    
    def pack(self):
        return struct.pack("I%dsI" % ADDRLENGTH, self.id,self.addr,self.port)
        
    def __str__(self):
        return 'PEER(%d, %s, %d)' % (self.id, self.addr, self.port)
    

    
        
        
