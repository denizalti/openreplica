'''
@author: denizalti
@note: The Leader
'''
from optparse import OptionParser
import threading
from Utils import *
from Connection import *
from Group import *
from Peer import *
from Message import *
from Acceptor import *
from Scout import *
from Commander import *

parser = OptionParser(usage="usage: %prog -i id -p port -b bootstrap")
parser.add_option("-i", "--id", action="store", dest="id", help="node id")
parser.add_option("-p", "--port", action="store", dest="port", help="port for the node")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port:id triple for the peer")
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
        # Synod Leader State
        self.ballotnumber = (self.id,0)
        self.pvalues = [] # array of pvalues
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
        returnstr = "State of Leader %d\n" %self.id
        returnstr += "IP: %s\n" % self.addr
        returnstr += "Port: %d\n" % self.port
        returnstr += "Acceptors:\n%s" % self.acceptors
        returnstr += "Leaders:\n%s" % self.leaders
        returnstr += "Replicas:\n%s" % self.replicas
        return returnstr
    
    def incrementBallotnumber(self):
        self.ballotnumber[1] += 1
        
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
            self.leaders = message.leaders
            self.acceptors = message.acceptors
            self.replicas = message.replicas
            print self.acceptors
        elif message.type == MSG_NEW:
            for leader in message.leaders:
                self.leaders.add(leader)
            for acceptor in message.acceptors:
                self.acceptors.add(acceptor)
            for replica in message.replicas:
                self.replicas.add(replica)
            print self.acceptors
        elif message.type == MSG_BYE:
            messagesource = Peer(message.source[0],message.source[1],message.source[2],message.source[3])
            if messagesource.type == ACCEPTOR:
                self.acceptors.remove(messagesource)
            elif messagesource.type == LEADER:
                self.leaders.remove(messagesource)
            else:
                self.replicas.remove(messagesource)
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
                    print "INPUT:", input
                    self.newCommand(int(commandnumber), proposal)
                elif input[0] == 'STATE':
                    print self
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
        print "To see my state type STATE"
        print "For help type HELP"
        print "To exit type EXIT"
    
    def newCommand(self,commandnumber,proposal):
        print "************New Command"
        replyFromScout = scoutReply()
        replyFromCommander = commanderReply()
        print "BALLOTNUMBER: ",self.ballotnumber
        chosenpvalue = PValue(ballotnumber=self.ballotnumber,commandnumber=commandnumber,proposal=proposal)
        scout = Scout(self.toPeer,self.acceptors,self.ballotnumber,replyFromScout)
        scout.start()
        # This is a busy-wait, should be optimized
        # Need Locks for Replies.
        while replyFromScout.type != 0 or replyFromCommander.type != 0:
            if replyFromScout.type != 0:
                if replyFromScout.type == SCOUT_ADOPTED:
                    possiblepvalues = []
                    for pvalue in replyFromScout.pvalues:
                        if pvalue.commandnumber == commandnumber:
                            possiblepvalues.append(pvalue)
                    if len(possiblepvalues) > 0:
                        chosenpvalue = max(possiblepvalues)
                    replyFromCommander = commanderReply()
                    commander = Commander(self.toPeer,self.acceptors,self.ballotnumber,chosenpvalue,replyFromCommander)
                    commander.start()
                    continue
                elif replyFromScout.type == SCOUT_PREEMPTED:
                    if replyFromScout.ballotnumber > self.ballotnumber:
                        self.incrementBallotnumber()
                        replyFromScout = scoutReply()
                        scout = Scout(self.toPeer,self.acceptors,self.ballotnumber,replyFromScout)
                        scout.start()

            elif replyFromCommander.type != 0:
                if replyFromCommander.type == COMMANDER_CHOSEN:
                    message = Message(type=MSG_PERFORM,source=self.leader.serialize,commandnumber=replyFromCommander[1],proposal=proposal)
                    self.replicas.broadcast(message)
                    break
                elif replyFromCommander.type == COMMANDER_PREEMPTED:
                    if replyFromScout.ballotnumber > self.ballotnumber:
                        self.incrementBallotnumber()
                        replyFromScout = scoutReply()
                        scout = Scout(self.toPeer,self.acceptors,self.ballotnumber,replyFromScout)
                        scout.start()
            else:
                print "DEBUG: Shouldn't reach here.."
        
   
'''main'''
def main():
    if options.bootstrap:
        theLeader = Leader(options.id,options.port,options.bootstrap)
    else:
        theLeader = Leader(options.id,options.port)

'''run'''
if __name__=='__main__':
    main()

  


    
