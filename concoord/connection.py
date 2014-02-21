'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Connections provide thread-safe send() and receive() functions, paying attention to message boundaries.
       ConnectionPools organize collections of connections.
@copyright: See LICENSE
'''
import sys
import socket, errno, select
import struct
import StringIO
import time
import msgpack
import random
from threading import Lock
from concoord.pack import *
from concoord.message import *
from concoord.exception import ConnectionError

class ConnectionPool():
    """ConnectionPool keeps the connections that a certain Node knows of.
    The connections can be indexed by a Peer instance or a socket."""
    def __init__(self):
        self.pool_lock = Lock()
        self.poolbypeer = {}
        self.poolbysocket = {}
        self.epoll = None
        self.epollsockets = {}
        # Sockets that are being actively listened to
        self.activesockets = set([])
        # Sockets that we didn't receive a msg on yet
        self.nascentsockets = set([])

    def add_connection_to_peer(self, peer, conn):
        """Adds a Connection to the ConnectionPool by its Peer"""
        if str(peer) not in self.poolbypeer:
            conn.peerid = str(peer)
            with self.pool_lock:
                conn.peerid = str(peer)
                self.poolbypeer[conn.peerid] = conn
                self.activesockets.add(conn.thesocket)
                if conn.thesocket in self.nascentsockets:
                    self.nascentsockets.remove(conn.thesocket)

    def del_connection_by_peer(self, peer):
        """ Deletes a Connection from the ConnectionPool by its Peer"""
        peerstr = str(peer)
        with self.pool_lock:
            if self.poolbypeer.has_key(peerstr):
                conn = self.poolbypeer[peerstr]
                del self.poolbypeer[peerstr]
                del self.poolbysocket[conn.thesocket.fileno()]
                if conn.thesocket in self.activesockets:
                    self.activesockets.remove(conn.thesocket)
                if conn.thesocket in self.nascentsockets:
                    self.nascentsockets.remove(conn.thesocket)
                conn.close()
            else:
                print "Trying to delete a non-existent connection from the connection pool."

    def del_connection_by_socket(self, thesocket):
        """ Deletes a Connection from the ConnectionPool by its Peer"""
        with self.pool_lock:
            if self.poolbysocket.has_key(thesocket.fileno()):
                connindict = self.poolbysocket[thesocket.fileno()]
                for connkey,conn in self.poolbypeer.iteritems():
                    if conn == connindict:
                        del self.poolbypeer[connkey]
                        break
                del self.poolbysocket[thesocket.fileno()]
                if thesocket in self.activesockets:
                    self.activesockets.remove(thesocket)
                if thesocket in self.nascentsockets:
                    self.nascentsockets.remove(thesocket)
                connindict.close()
            else:
                print "Trying to delete a non-existent socket from the connection pool."

    def get_connection_by_peer(self, peer):
        """Returns a Connection given corresponding Peer triple"""
        peerstr = str(peer)
        with self.pool_lock:
            if self.poolbypeer.has_key(peerstr):
                return self.poolbypeer[peerstr]
            else:
                try:
                    thesocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    thesocket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
                    thesocket.connect((peer[0], peer[1]))
                    thesocket.setblocking(0)
                    conn = Connection(thesocket, peerstr)
                    self.poolbypeer[peerstr] = conn
                    self.poolbysocket[thesocket.fileno()] = conn
                    if self.epoll:
                        self.epoll.register(thesocket.fileno(), select.EPOLLIN)
                        self.epollsockets[thesocket.fileno()] = thesocket
                    else:
                        self.activesockets.add(thesocket)
                        if thesocket in self.nascentsockets:
                            self.nascentsockets.remove(thesocket)
                    return conn
                except Exception as e:
                    return None

    def get_connection_by_socket(self, thesocket):
        """Returns a Connection given corresponding socket.
        A new Connection is created and added to the
        ConnectionPool if it doesn't exist.
        """
        with self.pool_lock:
            if self.poolbysocket.has_key(thesocket.fileno()):
                return self.poolbysocket[thesocket.fileno()]
            else:
                conn = Connection(thesocket)
                self.poolbysocket[thesocket.fileno()] = conn
                self.activesockets.add(thesocket)
                if thesocket in self.nascentsockets:
                    self.nascentsockets.remove(thesocket)
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
        # Rethink the size of the bytearray versus the
        # number of bytes requested in recv_into
        self.incomingbytearray = bytearray(100000)
        self.incoming = memoryview(self.incomingbytearray)
        self.incomingoffset = 0
        # Busy wait count
        self.busywait = 0

    def __str__(self):
        """Return Connection information"""
        if self.thesocket is None:
            return "Connection empty."
        return "Connection to Peer %s" % (self.peerid)

    # deprecated
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

    # used only while receiving a very large message
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
            datalen = 0
            try:
                datalen = self.thesocket.recv_into(self.incoming[self.incomingoffset:],
                                                   100000-self.incomingoffset)
            except IOError as inst:
                # [Errno 104] Connection reset by peer
                raise ConnectionError()

            if datalen == 0:
                if self.incomingoffset == 100000:
                    # buffer too small for a complete message
                    msg_length = struct.unpack("I", self.incoming[0:4].tobytes())[0]
                    msgstr = self.incoming[4:].tobytes()
                    try:
                        msgstr += self.receive_n_bytes(msg_length-(len(self.incoming)-4))
                        msgdict = msgpack.unpackb(msgstr, use_list=False)
                        self.incomingoffset = 0
                        yield parse_message(msgdict)
                    except IOError as inst:
                        self.incomingoffset = 0
                        raise ConnectionError()
                else:
                    raise ConnectionError()

            self.incomingoffset += datalen
            while self.incomingoffset >= 4:
                msg_length = (ord(self.incoming[3]) << 24) | (ord(self.incoming[2]) << 16) | (ord(self.incoming[1]) << 8) | ord(self.incoming[0])
                # check if there is a complete msg, if so return the msg
                # otherwise return None
                if self.incomingoffset >= msg_length+4:
                    msgdict = msgpack.unpackb(self.incoming[4:msg_length+4].tobytes(), use_list=False)
                    # this operation cuts the incoming buffer
                    if self.incomingoffset > msg_length+4:
                        self.incoming[:self.incomingoffset-(msg_length+4)] = self.incoming[msg_length+4:self.incomingoffset]
                    self.incomingoffset -= msg_length+4
                    yield parse_message(msgdict)
                else:
                    break

    def send(self, msg):
        with self.writelock:
            """pack and send a message on the Connection"""
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
                                self.busywait += 1
                                continue
                            else:
                                raise e
                return True
            except socket.error, e:
                 if isinstance(e.args, tuple):
                     if e[0] == errno.EPIPE:
                         return False
            except IOError, e:
                print "Send Error: ", e
            except AttributeError, e:
                pass
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
