'''
@author: denizalti
@note: The Acceptor acts like a server.
'''
from optparse import OptionParser
from threading import Thread
import threading
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
        self.addr = findOwnIP()
        self.port = int(port)
        self.id = int(id)
        self.type = ACCEPTOR
        self.toPeer = Peer(self.id,self.addr,self.port,self.type)
        # groups
        self.acceptors = Group(self.toPeer)
        self.replicas = Group(self.toPeer)
        self.leaders = Group(self.toPeer)
        # Synod Acceptor State
        self.ballotnumber = (0,0)
        self.accepted = [] # Array of pvalues
        # Exit
        self.run = True 
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
            helomessage = Message(type=MSG_HELO,source=self.toPeer.serialize())
            heloreply = self.acceptors.sendToPeer(bootpeer,helomessage)
            self.leaders.mergeList(heloreply.leaders)
            self.acceptors.mergeList(heloreply.acceptors)
            self.replicas.mergeList(heloreply.replicas)
            print str(self)
        # Start a thread with the server which will start a thread for each request
        server_thread = threading.Thread(target=self.serverloop)
        server_thread.start()
        # Start a thread that waits for inputs
        input_thread = threading.Thread(target=self.getInputs)
        input_thread.start()
        
    def __str__(self):
        returnstr = "State of Acceptor %d\n" %self.id
        returnstr += "IP: %s\n" % self.addr
        returnstr += "Port: %d\n" % self.port
        returnstr += "Acceptors:\n%s" % self.acceptors
        returnstr += "Leaders:\n%s" % self.leaders
        returnstr += "Replicas:\n%s" % self.replicas
        return returnstr
        
    def serverloop(self):
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
                Thread(target=self.handleconnection,args =[clientsock]).start()
            except KeyboardInterrupt:
                break
        s.close()
        return
        
    def handleconnection(self,clientsock):
#        print "DEBUG: Handling the connection.."
        addr,port = clientsock.getpeername()
        tuple = addr+":"+str(port)
        print tuple
        connection = Connection(addr,port,reusesock=clientsock)
        message = connection.receive()
        print message
        if message.type == MSG_HELO:
            messagesource = Peer(message.source[0],message.source[1],message.source[2],message.source[3])
            if messagesource.type == ACCEPTOR:
                self.acceptors.add(messagesource)
            elif messagesource.type == LEADER:
                self.leaders.add(messagesource)
            else:
                self.replicas.add(messagesource)
            print str(self)
            replymessage = Message(type=MSG_HELOREPLY,source=self.toPeer.serialize(),acceptors=self.acceptors.toList(),\
                                   leaders=self.leaders.toList(),replicas=self.replicas.toList())
            newmessage = Message(type=MSG_NEW,source=self.toPeer.serialize(),acceptors=self.acceptors.toList(),\
                                   leaders=self.leaders.toList(),replicas=self.replicas.toList())
            connection.send(replymessage)
            self.acceptors.broadcast(newmessage)
            self.leaders.broadcast(newmessage)
            self.replicas.broadcast(newmessage)
        elif message.type == MSG_HELOREPLY:
            self.leaders.mergeList(message.leaders)
            self.acceptors.mergeList(message.acceptors)
            self.replicas.mergeList(message.replicas)
        elif message.type == MSG_NEW:
            for leader in message.leaders:
                self.leaders.add(leader)
            for acceptor in message.acceptors:
                self.acceptors.add(acceptor)
            for replica in message.replicas:
                self.replicas.add(replica)
            print str(self)
        elif message.type == MSG_BYE:
            messagesource = Peer(message.source[0],message.source[1],message.source[2],message.source[3])
            if messagesource.type == ACCEPTOR:
                self.acceptors.remove(messagesource)
            elif messagesource.type == LEADER:
                self.leaders.remove(messagesource)
            else:
                self.replicas.remove(messagesource)
        elif message.type == MSG_PREPARE:
            if message.ballotnumber > self.ballotnumber:
                print "ACCEPTOR got a PREPARE with Ballotnumber: ", message.ballotnumber
                print "ACCEPTOR's Ballotnumber: ", self.ballotnumber
                print "This should be True: ", (message.ballotnumber > self.ballotnumber)
                self.ballotnumber = message.ballotnumber
                replymessage = Message(type=MSG_ACCEPT,source=self.toPeer.serialize(),ballotnumber=self.ballotnumber,givenpvalues=self.accepted)
            else:
                replymessage = Message(type=MSG_REJECT,source=self.toPeer.serialize(),ballotnumber=self.ballotnumber,givenpvalues=self.accepted)
            connection.send(replymessage)
        elif messagetype == MSG_PROPOSE:
            if message.ballotnumber >= self.ballotnumber:
                self.ballotnumber = message.ballotnumber
                newpvalue = PValue(ballotnumber=message.ballotnumber,commandnumber=message.commandnumber,proposal=message.proposal)
                self.accepted.append(newpvalue)
                replymessage = Message(type=MSG_ACCEPT,source=self.toPeer.serialize(),ballotnumber=self.ballotnumber,commandnumber=newpvalue.commandnumber)
            else:
                replymessage = Message(type=MSG_REJECT,source=self.toPeer.serialize(),ballotnumber=self.ballotnumber,commandnumber=newpvalue.commandnumber)
            connection.send(replymessage)
#        print "DEBUG: Closing the connection for %s:%d" % (addr,port)    
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
                elif input[0] == 'COMMAND':
                    commandnumber = input[1]
                    proposal = input[2]
                    self.newCommand(commandnumber, proposal)
                elif input[0] == 'STATE':
                    print self
                elif input[0] == 'PAXOS':
                    print self.accepted
                elif input[0] == 'EXIT':
                    print "So long and thanks for all the fish.."
                    self.die()
                else:
                    print "Sorry I couldn't get it.."
        return
                    
    def die(self):
        self.run = False
        byemessage = Message(type=MSG_BYE,source=self.toPeer.serialize())
        self.leaders.broadcast(byemessage)
        self.acceptors.broadcast(byemessage)
        self.replicas.broadcast(byemessage)
        self.leaders.sendToPeer(self.toPeer,byemessage)
                    
    def printHelp(self):
        print "I can execute a new Command for you as follows:"
        print "COMMAND commandnumber proposal"
        print "To see my Connection State type STATE"
        print "To see my Paxos State type PAXOS"
        print "For help type HELP"
        print "To exit type EXIT"
   
'''main'''
def main():
    if options.bootstrap:
        theNode = Acceptor(options.id,options.port,options.bootstrap)
    else:
        theNode = Acceptor(options.id,options.port)

'''run'''
if __name__=='__main__':
    main()

  


    
