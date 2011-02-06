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
from connection import ConnectionPool
from group import Group
from peer import Peer
from message import ClientMessage,Message,PaxosMessage,HandshakeMessage,PValue,PValueSet

# Class used to collect responses to both PREPARE and PROPOSE messages
class ResponseCollector():
    def __init__(self, acceptors, ballotno, commandnumber, proposal):
        self.ballotnumber = ballotno  # for sanity checking
        self.commandnumber = commandnumber
        self.proposal = proposal
        self.acceptors = acceptors
        self.ntotal = len(self.acceptors)
        self.nquorum = min(math.ceil(float(self.ntotal)/2+1), self.ntotal)

        self.possiblepvalueset = PValueSet()
        self.possiblepvalueset.add(PValue(ballotnumber=self.ballotnumber,commandnumber=commandnumber,proposal=proposal))
        self.nresponses = self.naccepts = self.rejects = 0

class Leader(Node):
    def __init__(self):
        Node.__init__(self, NODE_LEADER)
        # Synod Leader State
        self.ballotnumber = (0,self.id)
        self.pvalueset = PValueSet()

        self.commandnumber = 1  # incremented upon performing an operation
        self.outstandingprepares = {}
        self.outstandingproposes = {}
        
    def incrementBallotNumber(self):
        temp = (self.ballotnumber[0]+1,self.ballotnumber[1])
        self.ballotnumber = temp
        
    def getHighestCommandNumber(self):
        return max(k for k, v in self.requests.iteritems() if v != 0) if len(self.requests) > 0 else 1
        
    def msg_clientrequest(self, conn, msg):
        print "*** New Command ***"
        commandnumber = self.getHighestCommandNumber()
        proposal = msg.proposal
        self.doCommand(commandnumber, proposal)
        # XXX Right behavior should be implemented...
        clientreply = ClientMessage(MSG_CLIENTREPLY,self.me,"SUCCESS")
        conn.send(clientreply)

    def doCommand(self, commandnumber, proposal):
        myballotno = self.ballotnumber
        print "[%s] initiating command: %d:%s" % (self,commandnumber,proposal)
        print "[%s] try with ballotnumber %s" % (self,str(myballotno))
        prepare = PaxosMessage(MSG_PREPARE,self.me,myballotno)
        prc = ResponseCollector(self.groups[NODE_ACCEPTOR], myballotno, commandnumber, proposal)
        self.outstandingprepares[myballotno] = prc
        prc.acceptors.broadcast(self, prepare)
        print "[%s] did broadcast" % (self,)

    def msg_prepare_accept(self, conn, msg):
        if self.outstandingprepares.has_key(msg.inresponseto):
            prc = self.outstandingprepares[msg.inresponseto]
            print "[%s] got an accept for ballotno %s commandno %s proposal %s with %d out of %d" % (self, prc.ballotnumber, prc.commandnumber, prc.proposal, prc.nresponses, prc.ntotal)
            prc.nresponses += 1
            if msg.ballotnumber > prc.ballotnumber:
                print "!!!!!!!!!!!!!!!!! prc ballot number error, should not happen"

            prc.naccepts += 1
            # collect all the p-values from responses that have the same command number as me
            if msg.pvalueset is not None:
                for pvalue in msg.pvalueset.pvalues:
                    if pvalue.commandnumber == prc.commandnumber:
                        prc.possiblepvalueset.add(pvalue)

            print prc.nresponses, prc.nquorum
            if prc.nresponses >= prc.nquorum:
                print "[%s] suffiently many accepts on prepare" % (self,)
                # choose a p-value out of the set encountered and collected so far
                chosenpvalue = prc.possiblepvalueset.pickMaxBallotNumber()
                # take this response collector out of the outstanding prepare set
                del self.outstandingprepares[msg.inresponseto]
                # create a new response collector for the PROPOSE
                newprc = ResponseCollector(prc.acceptors, prc.ballotnumber, prc.commandnumber, prc.proposal)
                self.outstandingproposes[prc.ballotnumber] = newprc
                propose = PaxosMessage(MSG_PROPOSE,self.me,prc.ballotnumber,commandnumber=chosenpvalue.commandnumber,proposal=chosenpvalue.proposal)
                # send PROPOSE message
                prc.acceptors.broadcast(self, propose)
        else:
            print "[%s] there is no response collector" % (self,)

    def msg_prepare_reject(self, conn, msg):
        if self.outstandingprepares.has_key(msg.inresponseto):
            prc = self.outstandingprepares[msg.inresponseto]
            print "[%s] got a reject for ballotno %s commandno %s proposal %s with %d out of %d" % (self, prc.ballotnumber, prc.commandnumber, prc.proposal, prc.nresponses, prc.ntotal)
            # take this response collector out of the outstanding prepare set
            del self.outstandingprepares[msg.inresponseto]
            # increment the ballot number
            self.incrementBallotNumber()
            # retry the prepare
            doCommand(prc.commandnumber, prc.proposal)
        else:
            print "[%s] there is no response collector" % (self,)

    def msg_propose_accept(self, conn, msg):
        if self.outstandingproposes.has_key(msg.inresponseto):
            prc = self.outstandingproposes[msg.inresponseto]
            print "[%s] got an accept for proposal ballotno %s commandno %s proposal %s with %d out of %d" % (self, prc.ballotnumber, prc.commandnumber, prc.proposal, prc.nresponses, prc.ntotal)
            prc.nresponses += 1
            if msg.ballotnumber > prc.ballotnumber:
                print "!!!!!!!!!!!!!!!!! should not happen"
            prc.naccepts += 1
            if prc.nresponses >= prc.nquorum:
                # YAY, WE AGREE!
                self.incrementBallotNumber()
                # take this response collector out of the outstanding propose set
                del self.outstandingproposes[msg.inresponseto]
                # now we can perform this action on the replicas
                propose = PaxosMessage(MSG_PERFORM,self.me,commandnumber=prc.commandnumber,proposal=prc.proposal)
                self.groups[NODE_REPLICA].broadcast(self, propose)
        else:
            print "[%s] there is no response collector" % (self,)

    def msg_propose_reject(self, conn, msg):
        if self.outstandingproposes.has_key(msg.inresponseto):
            prc = self.outstandingproposes[msg.inresponseto]
            print "[%s] got a reject for proposal ballotno %s commandno %s proposal %s with %d out of %d" % (self, prc.ballotnumber, prc.commandnumber, prc.proposal, prc.nresponses, prc.ntotal)
            # take this response collector out of the outstanding propose set
            del self.outstandingproposes[msg.inresponseto]
            # increment the ballot number
            self.incrementBallotnumber()
            # retry the prepare
            doCommand(prc.commandnumber, prc.proposal)
        else:
            print "[%s] there is no response collector" % (self,)

    def cmd_command(self, args):
        commandnumber = args[1]
        proposal = ' '.join(args[2:])
        self.doCommand(int(commandnumber), proposal)
                    
def main():
    theLeader = Leader()
    theLeader.startservice()

if __name__=='__main__':
    main()
