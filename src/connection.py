import socket, errno
import struct
import time
import cPickle as pickle
import random

from threading import Lock
DEBUG=False
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
        print "_____________________________________________"
        print "ADDING CONNECTION TO PEER"
        connectionkey = peer.getid()
        self.poolbypeer[connectionkey] = conn
        print self
        print "_____________________________________________"
        
    def del_connection_by_peer(self, peer):
        """ Deletes a Connection from the ConnectionPool by its Peer"""
        connectionkey = peer.getid()
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
        print "_____________________________________________"
        print "GET CONNECTION TO PEER: ", peer
        print self
        print "_____________________________________________"
        connectionkey = peer.getid()
        if self.poolbypeer.has_key(connectionkey):
            return self.poolbypeer[connectionkey]
        else:
            thesocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            thesocket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
            thesocket.connect((peer.addr, peer.port))
            thesocket.setblocking(0)
            conn = Connection(thesocket)
            self.poolbypeer[connectionkey] = conn
            self.poolbysocket[thesocket] = conn
            return conn

    def get_connection_by_socket(self, thesocket):
        """Returns a Connection given corresponding socket.
        A new Connection is created and added to the
        ConnectionPool if it doesn't exist.
        """
        print "_____________________________________________"
        print "GET CONNECTION BY SOCKET: ", thesocket
        print self
        print "_____________________________________________"
        if self.poolbysocket.has_key(thesocket):
            return self.poolbysocket[thesocket]
        else:
            conn = Connection(thesocket)
            self.poolbysocket[thesocket] = conn
            return conn

    def __str__(self):
        """Returns ConnectionPool information"""
        peerstr= "\n".join(["%s: %s" % (str(peer), str(conn)) for peer,conn in self.poolbypeer.iteritems()])
        socketstr= "\n".join(["%s: %s" % (str(socket), str(conn)) for socket,conn in self.poolbysocket.iteritems()])
        temp = "Connection to Peers:\n%s\nConnection to Sockets:\n%s" %(peerstr, socketstr)
        return temp
        
class Connection():
    """Connection encloses the socket and send/receive functions for a connection."""
    def __init__(self, socket):
        """Initialize Connection"""
        self.thesocket = socket
        self.lock = Lock()
    
    def __str__(self):
        """Return Connection information"""
        try:
            return "Connection to Peer at addr: %s port: %d" % (self.thesocket.getpeername())
        except:
            return "NAMELESS SOCKET"
    
    def receive(self):
        with self.lock:
            """receive a message on the Connection"""
            try:
                returnstring = self.receive_n_bytes(4)
                msg_length = struct.unpack("I", returnstring[0:4])[0]
                msgstr = self.receive_n_bytes(msg_length)
                return (time.time(), pickle.loads(msgstr))
            except IOError as inst:
                print "Receive Error: ", inst            
                return (0,None)

    def receive_n_bytes(self, msg_length):
        msgstr = ''
        while len(msgstr) != msg_length:
            try:
                chunk = self.thesocket.recv(min(1024, msg_length-len(msgstr)))
            except IOError, e:
                if isinstance(e.args, tuple):
                    print e.args, errno.EDEADLK, errno.EAGAIN, errno.EBUSY
                    if e[0] == errno.EAGAIN:
                        continue
                    else:
                        print "Error during receive!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
                        raise e
            msgstr += chunk
        return msgstr
    
    def send(self, msg):
        with self.lock:
            """pickle and send a message on the Connection"""
            if DEBUG and random.random() <= DROPRATE:
                print "dropping message..."
                return
            messagestr = pickle.dumps(msg)
            messagelength = struct.pack("I", len(messagestr))
            print "MESSAGETOTAL: ", 4 + len(messagestr)
            try:
                totalsent = 0
                while totalsent < (4 + len(messagestr)):
                    print "Writing to ", str(self)
                    try:
                        bytesent = self.thesocket.send((messagelength + messagestr)[totalsent:])
                        print "Wrote %d bytes!" % bytesent
                        totalsent += bytesent
                        print "Total %d bytes!" % totalsent
                    except IOError, e:
                        if isinstance(e.args, tuple):
                            if e[0] == errno.EAGAIN:
                                continue
                            else:
                                raise e
                return True
            except socket.error, e:
                 if isinstance(e.args, tuple):
                     if e[0] == errno.EPIPE:
                         print "Remote disconnect"
                         return False
            except IOError, e:
                print "Send Error: ", e
            return False
    
    def settimeout(self, timeout):
        with self.lock:
            try:
                self.thesocket.settimeout(timeout)
            except socket.error, e:
                if isinstance(e.args, tuple):
                    if e[0] == errno.EBADF:
                        print "socket closed"

    def close(self):
        with self.lock:
            """Close the Connection"""
            self.thesocket.close()
            self.thesocket = None
