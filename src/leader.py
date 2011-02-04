'''
@author: denizalti
@note: The Leader
@date: February 1, 2011
'''
from optparse import OptionParser
from threading import Thread, Lock, Condition
import time
import random

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

parser = OptionParser(usage="usage: %prog -p port -b bootstrap -d delay")
parser.add_option("-p", "--port", action="store", dest="port", type="int", default=6668, help="port for the node")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port:type triple for the bootstrap peer")
(options, args) = parser.parse_args()

# TIMEOUT THREAD
class Leader():
    def __init__(self, port, bootstrap=None):
        self.addr = findOwnIP()
        self.port = port
        self.id = createID(self.addr,self.port)
        self.type = NODE_LEADER
        self.toPeer = Peer(self.id,self.addr,self.port,self.type)
        # groups
        self.groups = {NODE_ACCEPTOR:Group(self.toPeer),NODE_REPLICA:Group(self.toPeer),NODE_LEADER:Group(self.toPeer)}
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
        print "Leader Node %d: %s:%d" % (self.id,self.addr,self.port)
        if bootstrap:
            connectToBootstrap(self,bootstrap)
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
        for type,group in self.groups.iteritems():
            returnstr += str(group)
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
        time.sleep(delay)
        
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
                self.clients.add(messagesource)
            else:
                serialgroups = {}
                for type,group in self.groups.iteritems():
                    serialgroups[type] = group.toList()
                replymessage = Message(type=MSG_HELOREPLY,source=self.toPeer.serialize(),groups=serialgroups)
                newmessage = Message(type=MSG_NEW,source=self.toPeer.serialize(),newpeer=messagesource.serialize())
                for type,group in self.groups.iteritems():
                    group.broadcastNoReply(newmessage)
                self.groups[messagesource.type].add(messagesource)
            connection.send(replymessage)
        elif message.type == MSG_HELOREPLY:
            for type,group in self.groups.iteritems():
                group.mergeList(message.groups[type])
        elif message.type == MSG_NEW:
            newpeer = Peer(message.newpeer[0],message.newpeer[1],message.newpeer[2],message.newpeer[3])
            self.groups[newpeer.type].add(newpeer)
        elif message.type == MSG_CLIENTREQUEST:
            self.newCommand(self.getHighestCommandNumber(),message.proposal)
        elif message.type == MSG_BYE:
            messagesource = Peer(message.source[0],message.source[1],message.source[2],message.source[3])
            self.groups[messagesource.type].remove(messagesource)
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
                    proposal = input[2]+' '+input[3]
                    self.newCommand(int(commandnumber), proposal)
                elif input[0] == 'CONN':
                    print self
                elif input[0] == 'PAXOS':
                    print self.state
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
        print "I can execute a new Command for you as follows:"
        print "COMMAND commandnumber proposal"
        print "To see my Connection State type CONN"
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
                while replyFromScout.type == SCOUT_NOREPLY and replyFromCommander.type == SCOUT_NOREPLY:
                    self.replyCondition.wait()
                if replyFromScout.type != SCOUT_NOREPLY:
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
                elif replyFromCommander.type != SCOUT_NOREPLY:
                    print "There is a reply from Commander.."
                    if replyFromCommander.type == COMMANDER_CHOSEN:
                        message = Message(type=MSG_PERFORM,source=self.toPeer.serialize(),commandnumber=replyFromCommander.commandnumber,proposal=proposal)
                        self.replicas.broadcast(message)
                        self.incrementBallotNumber()
                        self.state[replyFromCommander.commandnumber] = proposal
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
        return
   
'''main'''
def main():
    theLeader = Leader(options.port,options.bootstrap)

'''run'''
if __name__=='__main__':
    main()
