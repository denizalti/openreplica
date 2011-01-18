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
from Generators import *
from Handlers import *
from Message import *

parser = OptionParser(usage="usage: %prog -i id -p port -t type -b bootstrap")
parser.add_option("-i", "--id", action="store", dest="id", help="node id")
parser.add_option("-p", "--port", action="store", dest="port", help="port for the node")
parser.add_option("-t", "--type", action="store", dest="type", help="type of the node")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port tuple for the peer")

(options, args) = parser.parse_args()

ACCEPTOR = 0
LEADER = 1
LEARNER = 2

# TIMEOUT THREAD
class Acceptor():
    def __init__(self, id, port, bootstrap=None):
        print "port: ", port
        print "id: ", id
        print "bootstrap: ", bootstrap
        self.addr = findOwnIP()
        self.port = int(port)
        self.ID = int(id)
        # neighbors
        self.neighborhoodSet = NeighborhoodSet()   # Keeps ID-Addr-Port
        # print some information
        print "DEBUG: IP: %s Port: %d ID: %d" % (self.addr,self.port,self.ID)
        if bootstrap:
            bootaddr,bootport,bootid = bootstrap.split(":")
            bootpeer = Peer(int(bootid),int(bootport),bootaddr)
            helomsg = self.create_helo('')
            self.neighborhoodSet.send_to_peer(bootpeer,helomsg)
        self.serverloop()
        
        # Synod Acceptor State
        self.ballot_num = 0
        self.accepted = None # Array of pvalues
        
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
        connection = Connection(addr,port,clientsock)
        msgtype,msg = connection.receive()
        try:
            msghandler = getattr(Handlers,"handle_"+msgtype)
        except AttributeError:
            print "Attribute Not Found"            
        result = msghandler(Handlers,msg)
        data = ''
        try: 
            msggenerator = getattr(Generators,"create_"+msgtype)
        except AttributeError:
            print "Attribute Not Found"
        msg = msggenerator(Handlers,data)
    
        print "DEBUG: Closing the connection for %s:%d" % (addr,port)    
        connection.close()
        
# MESSAGE HANDLERS
    def handle_prep(self,msg):
        print "DEBUG: received PREP msg"
        # When a PREPare msg is received, it indicates that the node is an acceptor
        # The following scenarios can apply:
        # 1) The proposal number N is greater than any previous proposal number: Acpt(LastValueAccepted)
        # 2) The proposal number N is less than a previous proposal number: Rjct()
        msg_type, msg_length, msg_number, msg_content = Message.unpack(Message, msg)
        
        if msg_number > self.highestballot:
            return ACPT
        else:
            return RJCT
        
    def handle_prop(self,msg):
        print "DEBUG: received PROP msg"
        # When a PROPose msg is received, it indicates that the proposer is proposing a value
        # The following scenarios can apply:
        # 1) The PROPose msg is for a proposal that has not been rejected: Acpt(LastValueAccepted)
        # 2) The PROPose msg is for a proposal that has been rejected: Rjct()
        msg_type, msg_length, msg_number, msg_content = Message.unpack(Message, msg)
        
        if msg_number > self.highestballot:
            return ACPT
        else:
            return RJCT
    
    def handle_done(self,msg):
        print "DEBUG: received DONE msg"
    
    def handle_rmve(self,msg):
        print "DEBUG: received RMVE msg"
    
    def handle_ping(self,msg):
        print "DEBUG: received PING msg"
    
    def handle_errr(self,msg):
        print "DEBUG: received ERRR msg"
        
# MESSAGE GENERATORS
    def create_helo(self):
        print "DEBUG: creating HELO msg"
        # HELO to the bootstrap
        Message.pack(HELO)
    
    def create_prep(self):
        print "DEBUG: creating PREP msg"
        Message.pack(PREP, self.ballot_num)
        self.ballot_num += 1
    
    def create_prop(self,value):
        print "DEBUG: creating PROP msg"
        Message.pack(PROP, self.ballot_num, value)
        self.ballot_num += 1
        
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
        theNode = Acceptor(options.id,options.port,options.bootstrap)
    else:
        theNode = Acceptor(options.id,options.port)

'''run'''
if __name__=='__main__':
    main()

  


    
