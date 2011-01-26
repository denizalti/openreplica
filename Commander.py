'''
@author: denizalti
@note: The Commander is responsible for
'''
import math
from threading import Thread,Lock,Condition
from Utils import *
from Connection import *
from Group import *
from Peer import *

class Commander(Thread):
    def __init__(self,leader,acceptors,ballotnum,pvalue,replyToLeader):
        Thread.__init__(self)
        self.leader = leader            # Peer()
        self.acceptors = acceptors      # Group()
        self.replyToLeader = replyToLeader
        # print some information
        print "DEBUG: Commander for Leader %d" % self.leader.id
        
        # Synod State
        self.pvalue = pvalue            # PValue()
        self.ballotnumber = ballotnum   # (leaderid,b)
        self.waitfor = math.ceil(len(self.acceptors)/2)
    
    def run(self):
        message = Message(type=MSG_PROPOSE,source=self.leader.serialize,ballotnumber=self.ballotnumber,\
                          commandnumber=self.pvalue.commandnumber,proposal=self.pvalue.proposal)
        replies = self.acceptors.broadcast(message)
        for reply in replies:
            self.changeState(reply)
            with self.replyToLeader.replyLock:
                if self.replyToLeader.type == SCOUT_BUSY:
                    continue
                else:
                    return
        
    def changeState(self, message):
        # Change State depending on the message
            print "Commander Changing State"
            if message.type == MSG_ACCEPT:
                if message.ballotnumber == self.ballotnumber:
                    self.waitfor -= 1
                    if self.waitfor < len(self.acceptors)/2:
                        with self.replyToLeader.replyLock:
                            self.replyToLeader.setType(COMMANDER_CHOSEN)
                            self.replyToLeader.setBallotnumber(self.ballotnumber)
                            self.replyToLeader.setCommandnumber(self.pvalue.commandnumber)
                            self.replyToLeader.replyCondition.notify()
                        return
                    else:
                        with self.replyToLeader.replyLock:
                            self.replyToLeader.setType(COMMANDER_BUSY)
                            self.replyToLeader.setBallotnumber(self.ballotnumber)
                            self.replyToLeader.replyCondition.notify()
                        return
                # There is a higher ballotnumber
                else:
                    with self.replyToLeader.replyLock:
                        self.replyToLeader.setType(COMMANDER_PREEMPTED)
                        self.replyToLeader.setBallotnumber(self.ballotnumber)
                        self.replyToLeader.replyCondition.notify()
                    return
            else:
                print "Commander Received.."
                print message
                
    def __str__(self):
        return "Commander for Leader %d" % self.leader.id