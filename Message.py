import struct

class Message():
    def __init__(self, type, n=0, v=None):
        self.type = type
        self.n = n
        self.v = v
        
    def pack(self, msg_type, n=0, v=None):
        msg_content = (n,v)
        msg_length = 4 + 4 + len(msg_content)
        temp = ""
        temp += struct.pack("I", msg_type)
        temp += struct.pack("I", msg_length)
        temp += msg_content 
        # XXX
        return temp
    
    # This method will work as a constructor
    # It will create the Message Object given the
    # received packet
    def unpack(self, msg):
        temp = msg
        msg_type = struct.unpack("I", temp[0:4])[0]
        temp = temp[4:]
        msg_length = struct.unpack("I", temp[0:4])[0]
        temp = temp[4:]
        msg_content = temp
        # XXX
        return (msg_type, msg_length, msg_content)
    
    def __str__(self):
        return 'MessageXXX(%s, %s, %d)' % (self.ID, self.addr, self.port)
    

    
        
        
