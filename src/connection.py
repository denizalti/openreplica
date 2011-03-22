import socket
import struct
import cPickle as pickle
import random

DEBUG=True
DROPRATE=0.3

class ConnectionPool():
    """ConnectionPool keeps the connections that a certain Node knows of.
    The connections can be indexed by a Peer instance or a socket."""
    def __init__(self):
        """Initialize ConnectionPool"""
        self.poolbypeer = {}
        self.poolbysocket = {}
        
    def add_connection_to_peer(self, peer, conn):
        """Adds a Connection to the ConnectionPool by its Peer"""
        connectionkey = peer.id()
        self.poolbypeer[connectionkey] = conn
        
    def del_connection_by_peer(self, peer):
        """ Deletes a Connection from the ConnectionPool by its Peer"""
        connectionkey = peer.id()
        if self.poolbypeer.has_key(connectionkey):
            conn = self.poolbypeer[connectionkey]
            del self.poolbypeer[connectionkey]
            del self.poolbysocket[conn.thesocket]
            conn.close()
        else:
            print "trying to delete a non-existent connection from the conn pool"

    def del_connection_by_socket(self, thesocket):
        """ Deletes a Connection from the ConnectionPool by its Peer"""
        if self.poolbysocket.has_key(thesocket):
            daconn = self.poolbysocket[thesocket]
            for connkey,conn in self.poolbypeer.iteritems():
                if conn == daconn:
                    del self.poolbypeer[connkey]
                    break
            del self.poolbysocket[daconn.thesocket]
            daconn.close()
        else:
            print "trying to delete a non-existent socket from the conn pool"

    def get_connection_by_peer(self, peer):
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

    def get_connection_by_socket(self, thesocket):
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

    def __str__(self):
        """Returns ConnectionPool information"""
        temp = "Connection to Peers:\n"
        for peer,conn in self.poolbypeer.iteritems():
            temp += str(peer)+"\n"
        temp += "Connection to Sockets:\n"
        for socket,conn in self.poolbypeer.iteritems():
            temp += str(socket)+"\n"
        return temp
        

class Connection():
    """Connection encloses the socket and send/receive functions for a connection."""
    def __init__(self, socket):
        """Initialize Connection"""
        self.thesocket = socket
    
    def __str__(self):
        """Return Connection information"""
        return "Connection to Peer at addr: %s port: %d" % (self.thesocket.getpeername())
    
    def receive(self):
        """receive a message on the Connection"""
        try:
            returnstring = self.thesocket.recv(4)
            if len(returnstring) < 4:
                print "receive too short"
                return None
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
        """pickle and send a message on the Connection"""
        #if DEBUG and random.random() <= DROPRATE:
        #    print "dropping message..."
        #    return
        messagestr = pickle.dumps(msg)
        messagelength = struct.pack("I", len(messagestr))
        try:
            self.thesocket.send(messagelength + messagestr)
        except IOError as inst:
            print "Send Error: ", inst
    
    def settimeout(self, timeout):
        self.thesocket.settimeout(timeout)

    def close(self):
        """Close the Connection"""
        self.thesocket.close()
        self.thesocket = None
