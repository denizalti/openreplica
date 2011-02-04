'''
@author: denizalti
@note: The Scout is responsible for
'''
from threading import Thread,Lock,Condition
import math
from enums import *
from utils import *
from connection import *
from group import *
from peer import *

class Scout(Thread):
    def __init__(self,leader,acceptors,ballotnum,replyToLeader):
        Thread.__init__(self)
        self.leader = leader
        self.acceptors = acceptors
        self.replyToLeader = replyToLeader
        # print some information
        print "DEBUG: Scout for Leader %d" % self.leader.id
        
        # Synod State
        self.pvalues = []
        self.ballotnumber = ballotnum
        self.waitfor = math.ceil(len(self.acceptors)/2)
        print "Scout has to wait for %d ACCEPTS.." % self.waitfor
    
    def run(self):
        message = Message(type=MSG_PREPARE,source=self.leader.serialize(),ballotnumber=self.ballotnumber)
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
                
    def __str__(self):
        return "Scout for Leader %d" % self.leader.id
    
    
    
