import socket
import struct
from Message import *

class ConnectionPool():
    def __init__(self):
        self.pool = {}
        
    def getConnection(self, addr, port):
        connectionkey = '%s:%d' % (addr,port)
        if self.pool.has_key(connectionkey):
            return self.pool[connectionkey]
        else:
            connection = Connection(addr,port)
            self.pool[connectionkey] = connection
            return connection
            
class Connection():
    def __init__(self, addr, port, reusesock=None):
        self.addr = addr
        self.port = port
        if reusesock == None:
#            print "DEBUG: A new socket is being created.."
            addr = addr.replace("\x00", "")
            self.thesocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.thesocket.connect((addr, port))
        else:
            self.thesocket = reusesock
    
    def get_details(self):
        print "The peer addr: %s port: %d" % (self.addr, self.port)
    
    def receive(self):
#        print "DEBUG: Receiving msg"
        try:
            returnstring = self.thesocket.recv(4)
            msg_length = struct.unpack("I", returnstring[0:4])[0]
            msg_length -= 4
            msg = ''
            while len(msg) != msg_length:
                chunk = self.thesocket.recv(min(1024, msg_length-len(msg)))
                if len(chunk) == 0:
                    break
                msg += chunk
            if len(msg) != msg_length:
                return None
        except Exception as inst:
            print inst     # the exception instance
            return None
        message = Message(serialmessage=returnstring[0:4]+msg)
#        print "DEBUG: %s" % message
        return message
    
    def send(self,msg):
#        print "DEBUG: Connection.send"
        message = msg.serialize()
        try:
            self.thesocket.send(message)
        except Exception as inst:
            print inst
            return False
        return True
    
    def close(self):
        self.thesocket.close()
        self.thesocket = None
        self.sd = None