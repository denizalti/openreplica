'''
@author: denizalti
@note: The Node is responsible for
        1) building and maintaining an unstructured mesh
        2) for forwarding queries along edges of the mesh
        3) responding to queries
'''
from optparse import OptionParser
import threading
from utils import *
from Connection import *
from NeighborhoodSet import *
from Peer import *

usage = "usage: %prog [options]"
parser = OptionParser()
parser.add_option("-p", "--port", action="store", dest="port", help="port for the node")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port tuple for the peer")

(options, args) = parser.parse_args()

# TIMEOUT THREAD
class Node():
    def __init__(self, id, port, bootstrap=None):
        self.addr = findOwnIP()
        self.port = int(port)
        self.ID = id
        # neighbors
        self.neighborhoodSet = NeighborhoodSet()   # Keeps ID-Addr-Port
        # print some information
        print "DEBUG: IP: %s Port: %d ID: %d" % (self.addr,self.port,self.ID)
        if bootstrap:
            bootaddr,bootport,bootid = bootstrap.split(":")
            bootpeer = Peer(bootaddr,int(bootport),int(bootid))
            hellomsg = self.create_helo('')
            self.neighborhoodSet.send_to_peer(bootpeer,hellomsg)
        self.serverloop()
        
        # Paxos State
        self.currentstate = None
        self.acceptedstate = None
        self.higheststatenumber = 0
        
    def serverloop(self):
        # wait for other peers to connect
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        s.bind((self.addr,self.port))
        s.listen(10)
#        s.settimeout(10)
        while True:
            try:
                clientsock,clientaddr = s.accept()
                print "DEBUG: Accepted a connection on socket:",clientsock," and address:",clientaddr
                # Start a Thread
                threading.Thread(target=self.handleconnection,args =[clientsock]).start()
            except KeyboardInterrupt:
                print 'DEBUG: Keyboard Interrupt..'
                continue
        s.close()
        
    def handleconnection(self,clientsock):
        print "DEBUG: Handling the connection.."
        addr,port = clientsock.getpeername()
        tuple = addr+":"+str(port)
        connection = Connection(addr, port, clientsock)
        msgtype,msg = connection.receive()
        try:
            m = getattr(self,"handle_"+msgtype)
        except AttributeError:
            print "Attribute Not Found"            
        result = m(self, msg)
        
        data = ''
        try: 
            msgcreate = getattr(self,"create_"+msgtype)
        except AttributeError:
            print "Attribute Not Found"
        msg = msgcreate(self, data)
    
        print "DEBUG: Closing the connection for %s:%d" % (addr,port)    
        connection.close()
    
# MESSAGE HANDLERS
    def handle_helo(self,msg):
        print "DEBUG: received HELO msg"
        # When a HELO msg is received it indicates that the node is a bootstrap node
        # So the Node receiving the HELO message should start the process for
        # reaching consensus
        n = self.higheststatenumber + 1
        data = n
        msgcreate = getattr(self, "create_prep")
        msg = msgcreate(self, data)
        prep_replies = self.neighborhoodSet.broadcast(msg)
        # Here broadcast returns (n,v) pairs received.
    
    def handle_prep(self,msg):
        print "DEBUG: received PREP msg"
    
    def handle_prop(self,msg):
        print "DEBUG: received PROP msg"
    
    def handle_cmmt(self,msg):
        print "DEBUG: received CMMT msg"
    
    def handle_acpt(self,msg):
        print "DEBUG: received ACPT msg"
    
    def handle_rjct(self,msg):
        print "DEBUG: received RJCT msg"
    
    def handle_done(self,msg):
        print "DEBUG: received DONE msg"
    
    def handle_rmve(self,msg):
        print "DEBUG: received RMVE msg"
    
    def handle_ping(self,msg):
        print "DEBUG: received PING msg"
    
    def handle_errr(self,msg):
        print "DEBUG: received ERRR msg"
   
# MESSAGE GENERATORS
    def create_helo(self,data):
        print "DEBUG: creating HELO msg"
    
    def create_prep(self,data):
        print "DEBUG: creating PREP msg"
    
    def create_prop(self,data):
        print "DEBUG: creating PROP msg"
    
    def create_cmmt(self,data):
        print "DEBUG: creating CMMT msg"
    
    def create_acpt(self,data):
        print "DEBUG: creating ACPT msg"
    
    def create_rjct(self,data):
        print "DEBUG: creating RJCT msg"
    
    def create_done(self,data):
        print "DEBUG: creating DONE msg"
    
    def create_rmve(self,data):
        print "DEBUG: creating RMVE msg"
    
    def create_ping(self,data):
        print "DEBUG: creating PING msg"
    
    def create_errr(self,data):
        print "DEBUG: creating ERRR msg"
   
'''main'''
def main():
    if options.bootstrap:
        print options.bootstrap
        theNode = Node(options.port, options.bootstrap)
    else:
        theNode = Node(options.port)

'''run'''
if __name__=='__main__':
    main()

  


    
