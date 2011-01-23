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
            print "+++++++++++++++++++"
            print heloreply
            print "+++++++++++++++++++"
            self.leaders = heloreply.leaders
            self.acceptors = heloreply.acceptors
            self.replicas = heloreply.replicas
            print "Now the Acceptors are:"
            print self.acceptors
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
            print "Source: ", message.source
            self.acceptors.add(Peer(message.source[0],message.source[1],message.source[2]))
            print "Now the Acceptors are:"
            print self.acceptors
            replymessage = Message(type=MSG_HELOREPLY,source=self.toPeer.serialize(),acceptors=self.acceptors.toList())
            newmessage = Message(type=MSG_NEW,source=self.toPeer.serialize(),acceptors=self.acceptors.toList())
            connection.send(replymessage)
            self.acceptors.broadcast(newmessage)
        elif message.type == MSG_HELOREPLY:
            print "HELOREPLY received.."
            self.leaders = message.leaders
            self.acceptors = message.acceptors
            self.replicas = message.replicas
            print self.acceptors
        elif message.type == MSG_NEW:
            print "NEW received.."
            for leader in message.leaders:
                self.leaders.add(leader)
            for acceptor in message.acceptors:
                self.acceptors.add(acceptor)
            for replica in message.replicas:
                self.replicas.add(replica)
            print self.acceptors
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

  


    
