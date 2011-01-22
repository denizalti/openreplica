'''
@author: denizalti
@note: The Commander is responsible for
'''
import math
from threading import Thread
from Utils import *
from Connection import *
from Group import *
from Peer import *

class Commander(Thread):
    def __init__(self,leader,acceptors,ballotnum,pvalue,replyToLeader):
        Thread.__init__(self)
        self.leader = leader            # Peer()
        self.acceptors = acceptors      # Group()
        # print some information
        print "DEBUG: Commander for Leader %d" % self.leader.id
        
        # Synod State
        self.pvalue = pvalue            # pvalue()
        self.ballotnumber = ballotnum   # (leaderid,b)
        self.commandnumber = self.pvalues
        self.waitfor = math.ceil(len(self.acceptors)/2)
    
    def run(self):
        message = Message(type=PROP,source=self.leader.serialize,ballotnumber=self.ballotnumber,givenpvalues=self.pvalues)
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
                if message.ballotnumber == self.ballotnumber:
                    self.waitfor -= 1
                    if self.waitfor < len(self.acceptors)/2:
                        return (COMMANDER_CHOSEN, self.commandnumber)
                    else:
                        return (SCOUT_BUSY, self.ballotnumber)
                # There is a higher ballotnumber
                else:
                    return (SCOUT_PREEMPTED, self.ballotnumber)
                
    def __str__(self):
        return "Commander for Leader %d" % self.leader.id