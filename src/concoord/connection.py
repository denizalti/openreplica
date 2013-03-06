'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Connections provide thread-safe send() and receive() functions, paying attention to message boundaries.
       ConnectionPools organize collections of connections.
@copyright: See LICENSE
'''
import sys
import socket, errno
import struct
import StringIO
import time
import msgpack
import random
from threading import Lock
from concoord.pack import *
from concoord.message import *

class ConnectionPool():
    """ConnectionPool keeps the connections that a certain Node knows of.
    The connections can be indexed by a Peer instance or a socket."""
    def __init__(self):
        self.poolbypeer = {}
        self.poolbysocket = {}
        self.pool_lock = Lock()
        self.activesockets = []
        
    def add_connection_to_peer(self, peer, conn):
        """Adds a Connection to the ConnectionPool by its Peer"""
        with self.pool_lock:
            self.poolbypeer[str(peer)] = conn
            conn.peerid = getpeerid(peer)
            self.activesockets.append(conn.thesocket)
            
    def del_connection_by_peer(self, peer):
        """ Deletes a Connection from the ConnectionPool by its Peer"""
        peerstr = str(peer)
        with self.pool_lock:
            if self.poolbypeer.has_key(peerstr):
                conn = self.poolbypeer[peerstr]
                del self.poolbypeer[peerstr]
                del self.poolbysocket[conn.thesocket]
                self.activesockets.remove(conn.thesocket)
                conn.close()
            else:
                print "Trying to delete a non-existent connection from the connection pool."
        
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
                self.activesockets.remove(daconn.thesocket)
                daconn.close()
            else:
                print "Trying to delete a non-existent socket from the connection pool."

    def get_connection_by_peer(self, peer):
        """Returns a Connection given corresponding Peer."""
        peerstr = str(peer)
        with self.pool_lock:
            if self.poolbypeer.has_key(peerstr):
                return self.poolbypeer[peerstr]
            else:
                try:
                    thesocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    thesocket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
                    thesocket.connect((peer.addr, peer.port))
                    thesocket.setblocking(0)
                    conn = Connection(thesocket, getpeerid(peer))
                    self.poolbypeer[peer] = conn
                    self.poolbysocket[thesocket] = conn
                    self.activesockets.append(thesocket)
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
                self.activesockets.append(thesocket)
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
        self.outgoing = ''
        self.incoming = ''
    
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
                msgdict = msgpack.unpackb(msgstr, use_list=False)
                return parse_message(msgdict)
            except IOError as inst:           
                return None

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
                raise IOError
            msgstr += chunk
        return msgstr

    def received_bytes(self):
        with self.readlock:
            rcvdmsgs = None
            # do the length business here
            temp = self.thesocket.recv(100000)
            if not temp:
                print "Connection closed"
                return False
            self.incoming += temp
            while len(self.incoming) >= 4:
                msg_length = struct.unpack("I", self.incoming[0:4])[0]
                # check if there is a complete msg, if so return the msg
                # otherwise return None
                if len(self.incoming) >= msg_length+4:
                    msgdict = msgpack.unpackb(self.incoming[4:msg_length+4], use_list=False)
                    self.incoming = self.incoming[msg_length+4:]
                    if rcvdmsgs:
                        rcvdmsgs.append(parse_message(msgdict))
                    else:
                        rcvdmsgs = [parse_message(msgdict)]
                else:
                    break
            return rcvdmsgs
    
    def send(self, msg):
        with self.writelock:
            """pickle and send a message on the Connection"""
            messagestr = msgpack.packb(msg)
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
                    print "Socket closed."

    def close(self):
        """Close the Connection"""
        self.thesocket.close()
        self.thesocket = None

    def _picklefixer(self, module, name):
        try:
            __import__(module)
        except:
            if module.split('.')[0] == 'concoord':
                module = module.split('.')[1]
            else:
                module = 'concoord.'+module
            __import__(module)
        return getattr(sys.modules[module], name)
        
