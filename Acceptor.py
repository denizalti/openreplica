'''
@author: denizalti
@note: The Acceptor acts like a server.
'''
from optparse import OptionParser
from threading import Thread
from Utils import *
from Connection import *
from Group import *
from Peer import *
from Message import *

parser = OptionParser(usage="usage: %prog -i id -p port -b bootstrap")
parser.add_option("-i", "--id", action="store", dest="id", help="node id")
parser.add_option("-p", "--port", action="store", dest="port", help="port for the node")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port:id triple for the peer")

(options, args) = parser.parse_args()

class Acceptor():
    def __init__(self, id, port, bootstrap=None):
        print "port: ", port
        print "id: ", id
        print "bootstrap: ", bootstrap
        self.addr = findOwnIP()
        self.port = int(port)
        self.id = int(id)
        self.toPeer = Peer(self.id,self.addr,self.port)
        # groups
        self.acceptors = Group()
        self.replicas = Group()
        self.leaders = Group()
        # print some information
        print "DEBUG: IP: %s Port: %d ID: %d" % (self.addr,self.port,self.id)
        if bootstrap:
            bootaddr,bootport,bootid = bootstrap.split(":")
            bootpeer = Peer(int(bootid),bootaddr,int(bootport))
            helomessage = Message(type=MSG_HELO,source=self.toPeer.serialize())
            heloreply = self.acceptors.send_to_peer(bootpeer,helomessage)
            print "HELO msg sent.."
        self.serverloop()
        
        # Synod Acceptor State
        self.ballotnumber = (0,0)
        self.accepted = None # Array of pvalues
        
    def serverloop(self):
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
                Thread(target=self.handleconnection,args =[clientsock]).start()
            except KeyboardInterrupt:
                break
        s.close()
        
    def handleconnection(self,clientsock):
        print "DEBUG: Handling the connection.."
        addr,port = clientsock.getpeername()
        tuple = addr+":"+str(port)
        print tuple
        connection = Connection(addr,port,reusesock=clientsock)
        message = connection.receive()
        print message
        if message.type == MSG_HELO:
            print "HELO received.."
            replymessage = Message(type=MSG_HELO)
            connection.send(replymessage)
        elif message.type == MSG_PREPARE:
            if message.ballotnumber > self.ballotnumber:
                self.ballotnumber = message.ballotnumber
                replymessage = Message(type=MSG_ACCEPT,source=self.toPeer.serialize(),ballotnumber=self.ballotnumber,givenpvalues=self.accepted)
            else:
                replymessage = Message(type=MSG_REJECT,source=self.toPeer.serialize(),ballotnumber=self.ballotnumber,givenpvalues=self.accepted)
            connection.send(replymessage)
        elif messagetype == MSG_PROPOSE:
            if message.ballotnumber >= self.ballotnumber:
                self.ballotnumber = message.ballotnumber
                newpvalue = pvalue(ballotnumber=message.ballotnumber,commandnumber=message.commandnumber,proposal=message.proposal)
                self.accepted.append(newpvalue)
                replymessage = Message(type=MSG_ACCEPT,source=self.toPeer.serialize(),ballotnumber=self.ballotnumber,commandnumber=newpvalue.commandnumber)
            else:
                replymessage = Message(type=MSG_REJECT,source=self.toPeer.serialize(),ballotnumber=self.ballotnumber,commandnumber=newpvalue.commandnumber)
            connection.send(replymessage)
        print "DEBUG: Closing the connection for %s:%d" % (addr,port)    
        connection.close()
   
'''main'''
def main():
    if options.bootstrap:
        theNode = Acceptor(options.id,options.port,options.bootstrap)
    else:
        theNode = Acceptor(options.id,options.port)

'''run'''
if __name__=='__main__':
    main()

  


    
