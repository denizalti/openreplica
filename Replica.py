'''
@author: denizalti
@note: The Leader
'''
from optparse import OptionParser
from threading import Thread, Lock, Condition
from Utils import *
import Connection
from Group import *
from Peer import *
from Message import *
from Acceptor import *
from Scout import *
from Commander import *
from Bank import *

parser = OptionParser(usage="usage: %prog -i id -p port -b bootstrap")
parser.add_option("-i", "--id", action="store", dest="id", help="node id")
parser.add_option("-p", "--port", action="store", dest="port", help="port for the node")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port:id:type for the bootstrap peer")
(options, args) = parser.parse_args()

# TIMEOUT THREAD
class Replica():
    def __init__(self, id, port, bootstrap=None):
        self.addr = findOwnIP()
        self.port = int(port)
        self.id = int(id)
        self.type = REPLICA
        self.toPeer = Peer(self.id,self.addr,self.port,self.type)
        # groups
        self.acceptors = Group(self.toPeer)
        self.replicas = Group(self.toPeer)
        self.leaders = Group(self.toPeer)
        # Exit
        self.run = True
        # Paxos State
        self.state = {}
        # Bank
        self.bank = Bank()
        # print some information
        print "DEBUG: IP: %s Port: %d ID: %d" % (self.addr,self.port,self.id)
        if bootstrap:
            bootaddr,bootport,bootid,boottype = bootstrap.split(":")
            bootpeer = Peer(int(bootid),bootaddr,int(bootport),int(boottype))
            if bootpeer.type == ACCEPTOR:
                self.acceptors.add(bootpeer)
            elif bootpeer.type == LEADER:
                self.leaders.add(bootpeer)
            else:
                self.replicas.add(bootpeer)
            heloMessage = Message(type=MSG_HELO,source=self.toPeer.serialize())
            heloReply = bootpeer.send(heloMessage)
            self.leaders.mergeList(heloReply.leaders)
            self.acceptors.mergeList(heloReply.acceptors)
            self.replicas.mergeList(heloReply.replicas)
            print str(self)
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
        returnstr += "Acceptors:\n%s" % self.acceptors
        returnstr += "Leaders:\n%s" % self.leaders
        returnstr += "Replicas:\n%s" % self.replicas
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
        tuple = addr+":"+str(port)
        connection = Connection.Connection(addr,port,reusesock=clientsock)
        message = connection.receive()
        if message.type == MSG_HELO:
            messageSource = Peer(message.source[0],message.source[1],message.source[2],message.source[3])
            if messageSource.type == ACCEPTOR:
                self.acceptors.add(messageSource)
            elif messageSource.type == LEADER:
                self.leaders.add(messageSource)
            else:
                self.replicas.add(messageSource)
            replymessage = Message(type=MSG_HELOREPLY,source=self.toPeer.serialize(),acceptors=self.acceptors.toList(),\
                                   leaders=self.leaders.toList(),replicas=self.replicas.toList())
            newmessage = Message(type=MSG_NEW,source=self.toPeer.serialize(),acceptors=self.acceptors.toList(),\
                                   leaders=self.leaders.toList(),replicas=self.replicas.toList())
            connection.send(replymessage)
            self.acceptors.broadcast(newmessage)
            self.leaders.broadcast(newmessage)
            self.replicas.broadcast(newmessage)
        elif message.type == MSG_HELOREPLY:
            self.leaders = message.leaders
            self.acceptors = message.acceptors
            self.replicas = message.replicas
        elif message.type == MSG_NEW:
            for leader in message.leaders:
                self.leaders.add(leader)
            for acceptor in message.acceptors:
                self.acceptors.add(acceptor)
            for replica in message.replicas:
                self.replicas.add(replica)
        elif message.type == MSG_DEBIT:
            randomleader = randint(0,len(self.leaders)-1)
            self.leaders[randomleader].send(message)
        elif message.type == MSG_DEPOSIT:
            randomleader = randint(0,len(self.leaders)-1)
            self.leaders[randomleader].send(message)
        elif message.type == MSG_BYE:
            messageSource = Peer(message.source[0],message.source[1],message.source[2],message.source[3])
            if messageSource.type == ACCEPTOR:
                self.acceptors.remove(messageSource)
            elif messageSource.type == LEADER:
                self.leaders.remove(messageSource)
            else:
                self.replicas.remove(messageSource)
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
                    self.newCommand(int(commandnumber), proposal)
                elif input[0] == 'STATE':
                    print self
                elif input[0] == 'PAXOS':
                    print self.state
                elif input[0] == 'EXIT':
                    print "So long and thanks for all the fish.."
                    self.die()
                else:
                    print "Sorry I couldn't get it.."
        return
                    
    def die(self):
        self.run = False
        byeMessage = Message(type=MSG_BYE,source=self.toPeer.serialize())
        self.leaders.broadcast(byeMessage)
        self.acceptors.broadcast(byeMessage)
        self.replicas.broadcast(byeMessage)
        self.toPeer.send(byeMessage)
                    
    def printHelp(self):
        print "I can execute a new Command for you as follows:"
        print "To see my Connection State type STATE"
        print "To see my Paxos State type PAXOS"
        print "For help type HELP"
        print "To exit type EXIT"
   
'''main'''
def main():
    theReplica = Replica(options.id,options.port,options.bootstrap)

'''run'''
if __name__=='__main__':
    main()

  


    
