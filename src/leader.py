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
        Node.__init__(self, NODE_LEADER)

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
        
    def msg_clientrequest(self, msg):
        print "*** New Command ***"
        commandnumber = self.getHighestCommandNumber()
        proposal = message.proposal
        self.doCommand(commandnumber, proposal)

        self.waitfor = math.ceil(len(self.acceptors)/2)
        print "Scout has to wait for %d ACCEPTS.." % self.waitfor
    
    # Scout thread, whose job is to ...
    def scout(self, args):
        message = PaxosMessage(MSG_PREPARE,self.leader.me,ballotnumber=self.ballotnumber)
        replies = self.groups[NODE_ACCEPTOR].acceptors.broadcast(message)
        for reply in replies:
            self.changeState(reply)
            with self.replyToLeader.replyLock:
                if self.replyToLeader.type == SCOUT_BUSY:
                    continue
                else:
                    return
        
    def changeState(self, message):
        # Change State depending on the message
            print "Scout Changing State"
            if message.type == MSG_ACCEPT:
                print "Got an ACCEPT Message" 
                if message.ballotnumber == self.ballotnumber:
                    print "with the same ballotnumber.."
                    self.pvalues = union(self.pvalues, message.pvalues)
                    self.waitfor -= 1
                    if self.waitfor < len(self.acceptors)/2:
                        with self.replyToLeader.replyLock:
                            self.replyToLeader.setType(SCOUT_ADOPTED)
                            self.replyToLeader.setBallotnumber(self.ballotnumber)
                            self.replyToLeader.setPValues(self.pvalues)
                            self.replyToLeader.replyCondition.notify()
                        return
                    else:
                        with self.replyToLeader.replyLock:
                            self.replyToLeader.setType(SCOUT_BUSY)
                            self.replyToLeader.setBallotnumber(self.ballotnumber)
                            self.replyToLeader.replyCondition.notify()
                        return
                # There is a higher ballotnumber
                else:
                    print "with another ballotnumber.."
                    with self.replyToLeader.replyLock:
                        self.replyToLeader.setType(SCOUT_PREEMPTED)
                        self.replyToLeader.setBallotnumber(self.ballotnumber)
                        self.replyToLeader.replyCondition.notify()
                    return
            else:
                print "Scout Received.."
                print message
                
    def doCommand(self, commandnumber, proposal):
        replyFromScout = scoutReply(self.replyLock,self.replyCondition)
        replyFromCommander = commanderReply(self.replyLock,self.replyCondition)
        print "BALLOTNUMBER: ",self.ballotnumber
        chosenpvalue = PValue(ballotnumber=self.ballotnumber,commandnumber=commandnumber,proposal=proposal)
        scout = Scout(self,self.ballotnumber,replyFromScout)
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
                    print "[%s] shouldn't reach here.." % self
        return
   
    def cmd_command(self, args):
        commandnumber = args[1]
        proposal = ' '.join(args[2:])
        self.doCommand(int(commandnumber), proposal)
                    
def main():
    theLeader = Leader()
    theLeader.startservice()

if __name__=='__main__':
    main()
