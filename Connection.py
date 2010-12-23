import socket
import struct

class Connection():
    def __init__( self,addr,port,ex_socket=None):
        self.addr = addr
        self.port = port
        if ex_socket==None:
            print "DEBUG: A new socket is being created.."
            addr = addr.replace("\x00", "")
            self.the_socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            self.the_socket.connect((addr, port))
        else:
            print "DEBUG: An existing socket is being used.."
            self.the_socket = ex_socket
    
        self.socket_file_desc = self.the_socket.makefile('rw', 0)
        
    def get_details(self):
        print "The peer name: %s addr: %s port: %d" % (self.peer_name, self.addr, self.port)
        
    def receive(self):
        print "DEBUG: Receiving msg"
        try:
            str = self.socket_file_desc.read(4)
            msg_type = struct.unpack("I", str[0:4])[0]
            msg_type = int(msg_type)
            if not msg_type:
                print "DEBUG: no msg_type in recvmsg" 
                return (None, None)
            str = self.socket_file_desc.read(4)
            msg_length = int(struct.unpack("I", str[0:4])[0])
            msg_length = msg_length-8
            msg = ""
            while len(msg) != msg_length:
                chunk = self.socket_file_desc.read(min(1024, msg_length-len(msg)))
                if len(chunk) == 0 :
                    break
                msg += chunk
            if len(msg) != msg_length:
                return (None, None)
        except:
            return (None, None)
        print "DEBUG: msg_type: %d msg_length: %d msg: %s" % (msg_type, msg_length, msg)
        return (msg_type, msg)
    
    def send(self,msg):
        try:
            self.socket_file_desc.write(msg)
            self.socket_file_desc.flush()
        except:
            print "DEBUG: in Connector.send msg cannot be sent"
            return False
        return True
    
    def close(self):
        self.the_socket.close()
        self.the_socket = None
        self.sd = None