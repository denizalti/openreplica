'''
@author: denizalti
@note: The Scout is responsible for
'''
import threading, math
from Utils import *
from Connection import *
from Group import *
from Peer import *

class Scout(Thread):
    def __init__(self,leader,acceptors,ballotnum,replyToLeader):
        Thread.__init__(self)
        self.leader = leader
        self.acceptors = acceptors
        # print some information
        print "DEBUG: Scout for Leader %d" % self.leader.id
        
        # Synod State
        self.pvalues = []
        self.ballotnumber = ballotnum
        self.waitfor = math.ceil(len(self.acceptors)/2)
    
    def run(self):
        message = Message(type=PREP,source=self.leader.serialize,ballotnumber=self.ballotnumber)
        replies = self.acceptors.broadcast(message)
        for reply in replies:
            returnvalue = self.changeState(reply)
            if returnvalue[0] == SCOUT_BUSY:
                continue
            else:
                replyToLeader = returnvalue
                return 0
        
    def changeState(self, message):
        # Change State depending on the message
            print "Scout Changing State"
            if message.type == MSG_ACCEPT:
                if message.ballot_num == self.ballot_num:
                    self.pvalues = union(self.pvalues, message.pvalues)
                    self.waitfor -= 1
                    if self.waitfor < len(self.acceptors)/2:
                        return (SCOUT_ADOPTED, self.ballot_num, self.pvalues)
                    else:
                        return (SCOUT_BUSY, self.ballot_num)
                # There is a higher ballotnumber
                else:
                    return (SCOUT_PREEMPTED, self.ballot_num)
                
    def __str__(self):
        return "Scout for Leader %d" % self.leader.id
