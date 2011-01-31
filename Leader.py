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
from time import sleep

parser = OptionParser(usage="usage: %prog -i id -p port -b bootstrap -d delay")
parser.add_option("-i", "--id", action="store", dest="id", help="node id")
parser.add_option("-p", "--port", action="store", dest="port", help="port for the node")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port:id:type for the bootstrap peer")
(options, args) = parser.parse_args()

# TIMEOUT THREAD
class Leader():
    def __init__(self, id, port, bootstrap=None):
        self.addr = findOwnIP()
        self.port = int(port)
        self.id = int(id)
        self.type = LEADER
        self.toPeer = Peer(self.id,self.addr,self.port,self.type)
        # groups
        self.acceptors = Group(self.toPeer)
        self.replicas = Group(self.toPeer)
        self.leaders = Group(self.toPeer)
        self.clients = Group(self.toPeer)
        # Synod Leader State
        self.ballotnumber = (self.id,0)
        self.pvalues = [] # array of pvalues
        # Condition Variable
        self.replyLock = Lock()
        self.replyCondition = Condition(self.replyLock)
        # Exit
        self.run = True
        # Paxos State
        self.state = {}
        # Bank
        self.bank = Bank()
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
        # Start a thread with the server which will start a thread for each request
        server_thread = Thread(target=self.serverLoop)
        server_thread.start()
        # Start a thread that waits for inputs
        input_thread = Thread(target=self.getInputs)
        input_thread.start()
        
    def __str__(self):
        returnstr = "State of Leader %d\n" %self.id
        returnstr += "IP: %s\n" % self.addr
        returnstr += "Port: %d\n" % self.port
        returnstr += "Acceptors:\n%s" % self.acceptors
        returnstr += "Leaders:\n%s" % self.leaders
        returnstr += "Replicas:\n%s" % self.replicas
        return returnstr
    
    def incrementBallotNumber(self):
        temp = (self.ballotnumber[0],self.ballotnumber[1]+1)
        self.ballotnumber = temp
        
    def getHighestCommandNumber(self):
        if len(self.state) == 0:
            return 1
        else:
            return max(k for k, v in self.state.iteritems() if v != 0)
        
    def wait(self, delay):
        sleep(delay)
        
    def serverLoop(self):
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        s.bind((self.addr,self.port))
        s.listen(10)
#        s.settimeout(10)
        while self.run:
            try:
                clientsock,clientaddr = s.accept()
                print "DEBUG: Accepted a connection on socket:",clientsock," and address:",clientaddr
                # Start a Thread
                Thread(target=self.handleConnection,args =[clientsock]).start()
            except KeyboardInterrupt:
                break
        s.close()
        return
        
    def handleConnection(self,clientsock):
        print "DEBUG: Handling the connection.."
        addr,port = clientsock.getpeername()
        connection = Connection.Connection(addr,port,reusesock=clientsock)
        print "Receiving message.."
        message = connection.receive()
        if message.type == MSG_HELO:
            messageSource = Peer(message.source[0],message.source[1],message.source[2],message.source[3])
            print "Message received from.."
            print messageSource
            replymessage = Message(type=MSG_HELOREPLY,source=self.toPeer.serialize(),acceptors=self.acceptors.toList(),\
                                   leaders=self.leaders.toList(),replicas=self.replicas.toList())
            newmessage = Message(type=MSG_NEW,source=self.toPeer.serialize(),acceptors=self.acceptors.toList(),\
                                   leaders=self.leaders.toList(),replicas=self.replicas.toList())
            connection.send(replymessage)
            print "Sending broadcast to everyone..."
            self.acceptors.broadcast(newmessage)
            self.leaders.broadcast(newmessage)
            self.replicas.broadcast(newmessage)
            if messageSource.type == ACCEPTOR:
                self.acceptors.add(messageSource)
            elif messageSource.type == LEADER:
                self.leaders.add(messageSource)
            elif messageSource.type == REPLICA:
                self.replicas.add(messageSource)
            elif messageSource.type == CLIENT:
                self.clients.add(messageSource)
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
            self.newCommand(self.getHighestCommandNumber(), "Debit")
        elif message.type == MSG_DEPOSIT:
            self.newCommand(self.getHighestCommandNumber(), "Deposit")
        elif message.type == MSG_BYE:
            messageSource = Peer(message.source[0],message.source[1],message.source[2],message.source[3])
            if messageSource.type == ACCEPTOR:
                self.acceptors.remove(messageSource)
            elif messageSource.type == LEADER:
                self.leaders.remove(messageSource)
            else:
                self.replicas.remove(messageSource)
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
                    self.newCommand(int(commandnumber), proposal)
                elif input[0] == 'STATE':
                    print self
                elif input[0] == 'PAXOS':
                    print self.pvalues
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
        print "COMMAND commandnumber proposal"
        print "To see my Connection State type STATE"
        print "To see my Paxos State type PAXOS"
        print "For help type HELP"
        print "To exit type EXIT"
    
    def newCommand(self,commandnumber,proposal):
        print "*** New Command ***"
        replyFromScout = scoutReply(self.replyLock,self.replyCondition)
        replyFromCommander = commanderReply(self.replyLock,self.replyCondition)
        print "BALLOTNUMBER: ",self.ballotnumber
        chosenpvalue = PValue(ballotnumber=self.ballotnumber,commandnumber=commandnumber,proposal=proposal)
        scout = Scout(self.toPeer,self.acceptors,self.ballotnumber,replyFromScout)
        scout.start()
        while True:
            with self.replyLock:
                while replyFromScout.type == 0 and replyFromCommander.type == 0:
                    self.replyCondition.wait()
                if replyFromScout.type != 0:
                    print "There is a reply from Scout.."
                    print replyFromScout
                    if replyFromScout.type == SCOUT_ADOPTED:
                        possiblepvalues = []
                        for pvalue in replyFromScout.pvalues:
                            if pvalue.commandnumber == commandnumber:
                                possiblepvalues.append(pvalue)
                        if len(possiblepvalues) > 0:
                            chosenpvalue = max(possiblepvalues)
                        replyFromCommander = commanderReply(self.replyLock,self.replyCondition)
                        replyFromScout = scoutReply(self.replyLock,self.replyCondition)
                        commander = Commander(self.toPeer,self.acceptors,self.ballotnumber,chosenpvalue,replyFromCommander)
                        commander.start()
                        print "Commander started.."
                        continue
                    elif replyFromScout.type == SCOUT_PREEMPTED:
                        if replyFromScout.ballotnumber > self.ballotnumber:
                            self.incrementBallotNumber()
                            replyFromScout = scoutReply(self.replyLock,self.replyCondition)
                            scout = Scout(self.toPeer,self.acceptors,self.ballotnumber,replyFromScout)
                            scout.start()
                elif replyFromCommander.type != 0:
                    print "There is a reply from Commander.."
                    if replyFromCommander.type == COMMANDER_CHOSEN:
                        message = Message(type=MSG_PERFORM,source=self.toPeer.serialize(),commandnumber=replyFromCommander.commandnumber,proposal=proposal)
                        self.replicas.broadcast(message)
                        self.incrementBallotNumber()
                        break
                    elif replyFromCommander.type == COMMANDER_PREEMPTED:
                        if replyFromScout.ballotnumber > self.ballotnumber:
                            self.incrementBallotNumber()
                            replyFromScout = scoutReply(self.replyLock,self.replyCondition)
                            scout = Scout(self.toPeer,self.acceptors,self.ballotnumber,replyFromScout)
                            scout.start()
                            replyFromScout.setType(0)
                            continue
                else:
                    print "DEBUG: Shouldn't reach here.."
        
   
'''main'''
def main():
    theLeader = Leader(options.id,options.port,options.bootstrap)

'''run'''
if __name__=='__main__':
    main()

  


    
