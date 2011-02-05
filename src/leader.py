'''
@author: denizalti
@note: The Leader
@date: February 1, 2011
'''
from threading import Thread, Lock, Condition
import time
import random
import math

from node import Node
from enums import *
from communicationutils import scoutReply,commanderReply
from connection import ConnectionPool
from group import Group
from peer import Peer
from message import Message,PaxosMessage,HandshakeMessage,PValue,PValueSet

class Leader(Node):
    def __init__(self):
        Node.__init__(self, NODE_LEADER)
        # Synod Leader State
        self.ballotnumber = (self.id,0)
        self.pvalueset = PValueSet()
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

    # Scout thread, whose job is to ...
    def scout(self,replyToLeader):
        print "[%s] scout" % self
        waitfor = math.ceil(float(len(self.groups[NODE_ACCEPTOR]))/2)
        message = PaxosMessage(MSG_PREPARE,self.me,self.ballotnumber)
        replies = self.groups[NODE_ACCEPTOR].broadcast(self,message)
        for reply in replies:
            self.scoutChangeState(reply,waitfor,replyToLeader)
            with replyToLeader.replyLock:
                if replyToLeader.type == SCOUT_BUSY:
                    continue
                else:
                    return

    def commander(self,replyToLeader,chosenpvalue):
        print "[%s] commander" % self
        waitfor = math.ceil(float(len(self.groups[NODE_ACCEPTOR]))/2)
        message = PaxosMessage(MSG_PROPOSE,self.me,self.ballotnumber,chosenpvalue.commandnumber,chosenpvalue.proposal)
        replies = self.groups[NODE_ACCEPTOR].broadcast(self,message)
        for reply in replies:
            self.commanderChangeState(reply,waitfor,replyToLeader,chosenpvalue)
            with replyToLeader.replyLock:
                if replyToLeader.type == COMMANDER_BUSY:
                    continue
                else:
                    return

    def commanderChangeState(self, message, waitfor, replyToLeader,chosenpvalue):
        if message.type == MSG_ACCEPT:
            if message.ballotnumber == self.ballotnumber:
                waitfor -= 1
                if waitfor < float(len(self.groups[NODE_ACCEPTOR]))/2:
                    with replyToLeader.replyLock:
                        replyToLeader.type = COMMANDER_CHOSEN
                        replyToLeader.ballotnumber = self.ballotnumber
                        replyToLeader.commandnumber = chosenpvalue.commandnumber
                        replyToLeader.replyCondition.notify()
                    return
                else:
                    with replyToLeader.replyLock:
                        self.replyToLeader.type = COMMANDER_BUSY
                        self.replyToLeader.ballotnumber = self.ballotnumber
                        self.replyToLeader.replyCondition.notify()
                    return
            # There is a higher ballotnumber
            else:
                with self.replyToLeader.replyLock:
                    self.replyToLeader.type = COMMANDER_PREEMPTED
                    self.replyToLeader.ballotnumber = self.ballotnumber
                    self.replyToLeader.replyCondition.notify()
                return
        else:
            print "[%s] commander received %s" % (self, message)

    def scoutChangeState(self, message, waitfor, replyToLeader):
        if message.type == MSG_ACCEPT:
            print "Got an ACCEPT Message" 
            if message.ballotnumber == self.ballotnumber:
                print "with the same ballotnumber.."
                self.pvalueset = self.pvalueset.union(message.pvalueset)
                waitfor -= 1
                if waitfor < float(len(self.groups[NODE_ACCEPTOR]))/2:
                    with replyToLeader.replyLock:
                        replyToLeader.type = SCOUT_ADOPTED
                        replyToLeader.ballotnumber = self.ballotnumber
                        replyToLeader.pvalueset = self.pvalueset
                        replyToLeader.replyCondition.notify()
                    return
                else:
                    with replyToLeader.replyLock:
                        replyToLeader.type = SCOUT_BUSY
                        replyToLeader.ballotnumber = self.ballotnumber
                        replyToLeader.replyCondition.notify()
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
            print "[%s] scout received %s" % (self, message)

    def doCommand(self, commandnumber, proposal):
        replyFromScout = scoutReply(self.replyLock,self.replyCondition)
        replyFromCommander = commanderReply(self.replyLock,self.replyCondition)
        print "BALLOTNUMBER: ",self.ballotnumber
        chosenpvalue = PValue(ballotnumber=self.ballotnumber,commandnumber=commandnumber,proposal=proposal)
        scout_thread = Thread(target=self.scout,args=[replyFromScout])
        scout_thread.start()
        while True:
            with self.replyLock:
                while replyFromScout.type == SCOUT_NOREPLY and replyFromCommander.type == SCOUT_NOREPLY:
                    self.replyCondition.wait()
                if replyFromScout.type != SCOUT_NOREPLY:
                    print "There is a reply from Scout.."
                    print replyFromScout
                    if replyFromScout.type == SCOUT_ADOPTED:
                        possiblepvalueset = PValueSet()
                        for pvalue in replyFromScout.pvalueset:
                            if pvalue.commandnumber == commandnumber:
                                possiblepvalueset.append(pvalue)
                        if len(possiblepvalueset) > 0:
                            chosenpvalue = possiblepvalueset.pvaluewithmaxballotnumber()
                        replyFromCommander = commanderReply(self.replyLock,self.replyCondition)
                        replyFromScout = scoutReply(self.replyLock,self.replyCondition)
                        commander_thread = Thread(target=self.commander,args=[replyFromCommander,chosenpvalue])
                        commander_thread.start()
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
                        message = PaxosMessage(MSG_PERFORM,self.me,commandnumber=replyFromCommander.commandnumber,proposal=proposal)
                        self.groups[NODE_REPLICA].broadcast(self,message)
                        self.incrementBallotNumber()
                        break
                    elif replyFromCommander.type == COMMANDER_PREEMPTED:
                        if replyFromScout.ballotnumber > self.ballotnumber:
                            self.incrementBallotNumber()
                            replyFromScout = scoutReply(self.replyLock,self.replyCondition)
                            scout_thread = Thread(target=self.scout,args=[replyFromScout])
                            scout_thread.start()
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
