'''
@author: denizalti
@note: The Leader
'''
from optparse import OptionParser
from threading import Thread, Lock, Condition
from enums import *
from utils import *
from communicationutils import *
from connection import *
from group import *
from peer import *
from message import *
from acceptor import *
from scout import *
from commander import *
from bank import *

parser = OptionParser(usage="usage: %prog -p port -b bootstrap")
parser.add_option("-p", "--port", action="store", dest="port", type="int", default=4448, help="port for the node")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port tuple for the bootstrap peer")
(options, args) = parser.parse_args()

# TIMEOUT THREAD
class Replica():
    def __init__(self, id, port, bootstrap=None):
        self.addr = findOwnIP()
        self.port = port
        self.id = createID(self.addr,self.port)
        self.type = NODE_REPLICA
        self.toPeer = Peer(self.id,self.addr,self.port,self.type)
        # groups
        self.groups = {NODE_ACCEPTOR:Group(self.toPeer),NODE_REPLICA:Group(self.toPeer),NODE_LEADER:Group(self.toPeer)}
        # Exit
        self.run = True
        # Bank
        self.bank = Bank()
        # print some information
        print "Replica Node %d: %s:%d" % (self.id,self.addr,self.port)
        if bootstrap:
            connectToBootstrap(self,bootstrap)
        # Start a thread with the server which will start a thread for each request
        server_thread = Thread(target=self.serverLoop)
        server_thread.start()
        # Start a thread that waits for inputs
        input_thread = Thread(target=self.getInputs)
        input_thread.start()
        
    def __str__(self):
        returnstr = "State of Replica %d\n" %self.id
        returnstr += "IP: %s\n" % self.addr
        returnstr += "Port: %d\n" % self.port
        for type,group in self.groups.iteritems():
            returnstr += str(group)
        return returnstr
        
    def serverLoop(self):
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        s.bind((self.addr,self.port))
        s.listen(10)
#        s.settimeout(10)
        while self.run:
            try:
                clientsock,clientaddr = s.accept()
#                print "DEBUG: Accepted a connection on socket:",clientsock," and address:",clientaddr
                # Start a Thread
                Thread(target=self.handleConnection,args =[clientsock]).start()
            except KeyboardInterrupt:
                break
        s.close()
        return
        
    def handleConnection(self,clientsock):
#        print "DEBUG: Handling the connection.."
        addr,port = clientsock.getpeername()
        connection = Connection(addr,port,reusesock=clientsock)
        message = Message(connection.receive())
        if message.type == MSG_HELO:
            messagesource = Peer(message.source[0],message.source[1],message.source[2],message.source[3])
            if messagesource.type == NODE_CLIENT:
                replymessage = Message(type=MSG_HELOREPLY,source=self.toPeer.serialize())
            else:
                serialgroups = {}
                for type,group in self.groups.iteritems():
                    serialgroups[type] = group.toList()
                replymessage = Message(type=MSG_HELOREPLY,source=self.toPeer.serialize(),groups=serialgroups)
            newmessage = Message(type=MSG_NEW,source=self.toPeer.serialize(),newpeer=messagesource.serialize())
            connection.send(replymessage)
            # Broadcasting MSG_NEW without waiting for a reply.
            # To add replies, first we have to add MSG_ACK & MSG_NACK
            for type,group in self.groups.iteritems():
                group.broadcastNoReply(newmessage)
            self.groups[messagesource.type].add(messagesource)
        elif message.type == MSG_HELOREPLY:
            for type,group in self.groups.iteritems():
                group.mergeList(message.groups[type])
        elif message.type == MSG_NEW:
            newpeer = Peer(message.newpeer[0],message.newpeer[1],message.newpeer[2],message.newpeer[3])
            self.groups[newpeer.type].add(newpeer)
        elif message.type == MSG_CLIENTREQUEST:
            randomleader = randint(0,len(self.leaders)-1)
            self.groups[NODE_LEADER].members[randomleader].send(message)
        elif message.type == MSG_BYE:
            messagesource = Peer(message.source[0],message.source[1],message.source[2],message.source[3])
            self.groups[messagesource.type].remove(messagesource)
        elif message.type == MSG_PERFORM:
            self.state[message.commandnumber] = message.proposal
            self.bank.executeCommand(message.proposal)
        connection.close()
        
    def getInputs(self):
        while self.run:
            input = raw_input("What should I do? ")
            if len(input) == 0:
                print "I'm listening.."
            else:
                input = input.split()
                input[0] = input[0].upper()
                if input[0] == 'HELP':
                    self.printHelp()
                elif input[0] == 'CONN':
                    print self
                elif input[0] == 'BANK':
                    print self.bank
                elif input[0] == 'EXIT':
                    self.die()
                else:
                    print "Sorry I couldn't get it.."
        return
                    
    def die(self):
        self.run = False
        byeMessage = Message(type=MSG_BYE,source=self.toPeer.serialize())
        for type,group in self.groups.iteritems():
            group.broadcast(byeMessage)
        self.toPeer.send(byeMessage)
                    
    def printHelp(self):
        print "To see my Connection State type CONN"
        print "To see my Bank State type BANK"
        print "For help type HELP"
        print "To exit type EXIT"
   
'''main'''
def main():
    theReplica = Replica(options.port,options.bootstrap)

'''run'''
if __name__=='__main__':
    main()

  


    
