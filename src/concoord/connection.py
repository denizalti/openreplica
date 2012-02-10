'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Connections provide thread-safe send() and receive() functions, paying attention to message boundaries.
       ConnectionPools organize collections of connections.
@date: February 3, 2011
@copyright: See LICENSE
'''
import sys
import socket, errno
import struct
import StringIO
import time
import cPickle
import random
from threading import Lock

DEBUG=False
DROPRATE=0.3

class ConnectionPool():
    """ConnectionPool keeps the connections that a certain Node knows of.
    The connections can be indexed by a Peer instance or a socket."""
    def __init__(self):
        self.poolbypeer = {}
        self.poolbysocket = {}
        self.pool_lock = Lock()
        
    def add_connection_to_peer(self, peer, conn):
        """Adds a Connection to the ConnectionPool by its Peer"""
        with self.pool_lock:
            connectionkey = peer.getid()
            self.poolbypeer[connectionkey] = conn
            conn.peerid = connectionkey
            
    def del_connection_by_peer(self, peer):
        """ Deletes a Connection from the ConnectionPool by its Peer"""        
        with self.pool_lock:
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
        with self.pool_lock:
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
        with self.pool_lock:
            connectionkey = peer.getid()
            if self.poolbypeer.has_key(connectionkey):
                return self.poolbypeer[connectionkey]
            else:
                try:
                    thesocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    thesocket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
                    thesocket.connect((peer.addr, peer.port))
                    thesocket.setblocking(0)
                    conn = Connection(thesocket, connectionkey)
                    self.poolbypeer[connectionkey] = conn
                    self.poolbysocket[thesocket] = conn
                    return conn
                except:
                    return None

    def get_connection_by_socket(self, thesocket):
        """Returns a Connection given corresponding socket.
        A new Connection is created and added to the
        ConnectionPool if it doesn't exist.
        """
        with self.pool_lock:
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
    def __init__(self, socket, peerid=None):
        """Initialize Connection"""
        self.thesocket = socket
        self.peerid = peerid
        self.readlock = Lock()
        self.writelock = Lock()
    
    def __str__(self):
        """Return Connection information"""
        if self.thesocket is None:
            return ""
        return "Connection to Peer %s" % (self.peerid)
    
    def receive(self):
        with self.readlock:
            """receive a message on the Connection"""
            try:
                lstr = self.receive_n_bytes(4)
                msg_length = struct.unpack("I", lstr[0:4])[0]
                msgstr = self.receive_n_bytes(msg_length)
                pickle_obj = cPickle.Unpickler(StringIO.StringIO(msgstr))
                pickle_obj.find_global = self._picklefixer
                return (time.time(), pickle_obj.load())
            except IOError as inst:           
                return (0,None)

    def receive_n_bytes(self, msg_length):
        msgstr = ''
        while len(msgstr) != msg_length:
            try:
                chunk = self.thesocket.recv(min(1024, msg_length-len(msgstr)))
            except IOError, e:
                if isinstance(e.args, tuple):
                    if e[0] == errno.EAGAIN:
                        continue
                raise e
            if len(chunk) == 0:
                print "Connection closed.."
                raise IOError
            msgstr += chunk
        return msgstr
    
    def send(self, msg):
        with self.writelock:
            """pickle and send a message on the Connection"""
            if DEBUG and random.random() <= DROPRATE:
                print "dropping message..."
                return
            messagestr = cPickle.dumps(msg)
            message = struct.pack("I", len(messagestr)) + messagestr
            try:
                while len(message) > 0:
                    try:
                        bytesent = self.thesocket.send(message)
                        message = message[bytesent:]
                    except IOError, e:
                        if isinstance(e.args, tuple):
                            if e[0] == errno.EAGAIN:
                                continue
                            else:
                                raise e
                    except AttributeError, e:
                        raise e
                return True
            except socket.error, e:
                 if isinstance(e.args, tuple):
                     if e[0] == errno.EPIPE:
                         print "Remote disconnect"
                         return False
            except IOError, e:
                print "Send Error: ", e
            except AttributeError, e:
                print "Socket deleted."
            return False
    
    def settimeout(self, timeout):
        try:
            self.thesocket.settimeout(timeout)
        except socket.error, e:
            if isinstance(e.args, tuple):
                if e[0] == errno.EBADF:
                    print "socket closed"

    def close(self):
        """Close the Connection"""
        self.thesocket.close()
        self.thesocket = None

    def _picklefixer(self, module, name):
        try:
            __import__(module)
        except:
            module = 'concoord.'+module
            __import__(module)
        return getattr(sys.modules[module], name)
        
