import socket
import struct
import cPickle as pickle

class ConnectionPool():
    def __init__(self):
        self.poolbypeer = {}
        
    def getConnectionToPeer(self, peer):
        connectionkey = peer.id()
        if self.poolbypeer.has_key(connectionkey):
            return self.poolbypeer[connectionkey]
        else:
            thesocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            thesocket.connect((peer.addr, peer.port))
            conn = Connection(thesocket)
            self.poolbypeer[connectionkey] = conn
            return conn
            
class Connection():
    def __init__(self, socket):
        self.thesocket = socket
    
    def __str__(self):
        return "Connection with Peer at addr: %s port: %d" % (self.addr, self.port)
    
    def receive(self):
        try:
            returnstring = self.thesocket.recv(4)
            msg_length = struct.unpack("I", returnstring[0:4])[0]
            msgstr = ''
            while len(msgstr) != msg_length:
                chunk = self.thesocket.recv(min(1024, msg_length-len(msgstr)))
                if len(chunk) == 0:
                    break
                msgstr += chunk
            if len(msgstr) != msg_length:
                return None
            return pickle.loads(msgstr)
        except IOError as inst:
            print "Receive Error: ", inst
            return None
    
    def send(self, msg):
        messagestr = pickle.dumps(msg)
        messagelength = struct.pack("I", len(messagestr))
        try:
            self.thesocket.send(messagelength + messagestr)
        except IOError as inst:
            print "Send Error: ", inst
    
    def close(self):
        self.thesocket.close()
        self.thesocket = None
        self.sd = None
