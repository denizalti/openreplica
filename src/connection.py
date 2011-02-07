import socket
import struct
import cPickle as pickle

class ConnectionPool():
    """ConnectionPool keeps the connections that a certain Node knows of.
    The connections can be indexed by a Peer instance or a socket."""
    def __init__(self):
        """Initialize ConnectionPool"""
        self.poolbypeer = {}
        self.poolbysocket = {}
        
    def addConnectionToPeer(self, peer, conn):
        """Adds a Connection to the ConnectionPool by its Peer"""
        connectionkey = peer.id()
        self.poolbypeer[connectionkey] = conn
        
    def getConnectionToPeer(self, peer):
        """Returns a Connection given corresponding Peer.
        A new Connection is created and added to the
        ConnectionPool if it doesn't exist.
        """
        connectionkey = peer.id()
        if self.poolbypeer.has_key(connectionkey):
            return self.poolbypeer[connectionkey]
        else:
            thesocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            thesocket.connect((peer.addr, peer.port))
            conn = Connection(thesocket)
            self.poolbypeer[connectionkey] = conn
            self.poolbysocket[thesocket] = conn
            return conn

    def getConnectionBySocket(self, thesocket):
        """Returns a Connection given corresponding socket.
        A new Connection is created and added to the
        ConnectionPool if it doesn't exist.
        """
        if self.poolbysocket.has_key(thesocket):
            return self.poolbysocket[thesocket]
        else:
            conn = Connection(thesocket)
            self.poolbysocket[thesocket] = conn
            return conn

class Connection():
    """Connection encloses the socket and send/receive functions for a connection."""
    def __init__(self, socket):
        """Initialize Connection"""
        self.thesocket = socket
    
    def __str__(self):
        """Return Connection information"""
        return "Connection with Peer at addr: %s port: %d" % (self.thesocket.getsockname())
    
    def receive(self):
        """receive a message on the Connection"""
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
        """pickle and send a message on yje Connection"""
        messagestr = pickle.dumps(msg)
        messagelength = struct.pack("I", len(messagestr))
        try:
            self.thesocket.send(messagelength + messagestr)
        except IOError as inst:
            print "Send Error: ", inst
    
    def close(self):
        """Close the Connection"""
        self.thesocket.close()
        self.thesocket = None
