'''
@author: denizalti
@note: The Leader
@date: February 1, 2011
'''
from threading import Thread, Lock, Condition
import time
import random
from node import Node
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

class Leader(Node):
    def __init__(self):
        Node.__init__(self)
        # Synod Leader State
        self.ballotnumber = (self.id,0)
        self.pvalues = [] # array of pvalues
        # Condition Variable
        self.replyLock = Lock()
        self.replyCondition = Condition(self.replyLock)
        
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
        
    def handleConnection(self,clientsock):
#        print "DEBUG: Handling the connection.."
        addr,port = clientsock.getpeername()
        connection = Connection(addr,port,reusesock=clientsock)
        message = Message(connection.receive())
        print "%s got message %s" % (self, message)
        if message.type == MSG_HELO:
            # The message source here will be changed.
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
   
    def cmd_command(self, args):
        commandnumber = args[1]
        proposal = args[2] + ' ' + args[3]
        self.newCommand(int(commandnumber), proposal)
                    
def main():
    theLeader = Leader()
    theLeader.startservice()

if __name__=='__main__':
    main()
