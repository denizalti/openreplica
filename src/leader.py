"""
@author: denizalti
@note: The Leader
@date: February 1, 2011
"""
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
    """ResponseCollector keeps the state related to both MSG_PREPARE and
    MSG_PROPOSE.
    """
    def __init__(self, acceptors, ballotno, commandnumber, proposal):
        """Initialize ResponseCollector

        ResponseCollector State
        - ballotnumber: ballotnumber for the corresponding MSG
        - commandnumber: commandnumber for the corresponding MSG
        - proposal: proposal for the corresponding MSG
        - acceptors: Group of Acceptor nodes for the corresponding MSG
        - ntotal: # Acceptor nodes for the corresponding MSG
        - nquorum: # ACCEPTs needed for success
        - nresponses: # responses received thus far
        - naccepts: # accepts received thus far
        - nrejects: # rejects received thus far

        - possiblepvalueset: Set of pvalues collected from Acceptor nodes
        with the matching commandnumber as the MSG
        """
        self.ballotnumber = ballotno
        self.commandnumber = commandnumber
        self.proposal = proposal
        self.acceptors = acceptors
        self.ntotal = len(self.acceptors)
        self.nquorum = min(math.ceil(float(self.ntotal)/2+1), self.ntotal)

        self.possiblepvalueset = PValueSet()
        self.possiblepvalueset.add(PValue(ballotnumber=self.ballotnumber,commandnumber=commandnumber,proposal=proposal))
        self.nresponses = self.naccepts = self.rejects = 0

class Leader(Node):
    """Leader extends a Node and keeps additional state about the Paxos Protocol and Commands in progress."""
    def __init__(self):
        """Initialize Leader

        Leader State
        - ballotnumber: the highest ballotnumber Leader has used
        - pvalueset: the PValueSet for Leader, which encloses all
        (ballotnumber,commandnumber,proposal) triples Leader knows about
        - commandnumber: the highest commandnumber Leader knows about
        - outstandingprepares: ResponseCollector dictionary for MSG_PREPARE,
        indexed by ballotnumber
        - outstandingproposes: ResponseCollector dictionary for MSG_PROPOSE,
        indexed by ballotnumber
        """
        Node.__init__(self, NODE_LEADER)
        self.ballotnumber = (0,self.id)
        self.pvalueset = PValueSet()

        self.commandnumber = 1  # incremented upon performing an operation
        self.outstandingprepares = {}
        self.outstandingproposes = {}
        
    def incrementBallotNumber(self):
        """Increment the numeric part of the ballotnumber."""
        temp = (self.ballotnumber[0]+1,self.ballotnumber[1])
        self.ballotnumber = temp
        
    def getHighestCommandNumber(self):
        """Return the highest Commandnumber the Leader knows of."""
        return max(k for k, v in self.requests.iteritems() if v != 0) if len(self.requests) > 0 else 1
        
    def msg_clientrequest(self, conn, msg):
        """Handler for a CLIENTREQUEST
        A new Paxos Protocol is initiated with the first available commandnumber
        the Leader knows of.
        """
        print "[%s] Initiating a New Command" % self
        commandnumber = self.getHighestCommandNumber()
        proposal = msg.proposal
        self.doCommand(commandnumber, proposal)
        # XXX Right behavior should be implemented...
        clientreply = ClientMessage(MSG_CLIENTREPLY,self.me,"SUCCESS")
        conn.send(clientreply)

    def doCommand(self, commandnumber, proposal):
        """Do a command with the given commandnumber and proposal.
        A command is initiated by running a Paxos Protocol for the command.

        State Updates:
        - Start the PREPARE STAGE:
        -- create MSG_PREPARE: message carries the corresponding ballotnumber Then a new
        -- create ResponseCollector object for PREPARE STAGE: ResponseCollector keeps
        the state related to MSG_PREPARE
        -- add the ResponseCollector to the outstanding prepare set
        -- broadcast MSG_PREPARE to Acceptor nodes
        """
        myballotno = self.ballotnumber
        print "[%s] initiating command: %d:%s" % (self,commandnumber,proposal)
        print "[%s] try with ballotnumber %s" % (self,str(myballotno))
        prepare = PaxosMessage(MSG_PREPARE,self.me,myballotno)
        prc = ResponseCollector(self.groups[NODE_ACCEPTOR], myballotno, commandnumber, proposal)
        self.outstandingprepares[myballotno] = prc
        prc.acceptors.broadcast(self, prepare)

    def msg_prepare_accept(self, conn, msg):
        """Handler for MSG_PREPARE_ACCEPT
        MSG_PREPARE_ACCEPT is handled only if it belongs to an outstanding MSG_PREPARE,
        otherwise it is discarded.
        When MSG_PREPARE_ACCEPT is received, the corresponding ResponseCollector is retrieved
        and its state is updated accordingly.

        State Updates:
        - nresponses and naccepts are incremented
        - the pvalue with the ResponseCollector's commandnumber is added to the possiblepvalueset
        - if naccepts is greater than the quorum size PREPARE STAGE is successful.
        -- Start the PROPOSE STAGE:
        --- choose the pvalue that has to be proposed (to avoid multiple proposals for one commandnumber)
        --- remove the old ResponseCollector from the outstanding prepare set
        --- create ResponseCollector object for PROPOSE STAGE: ResponseCollector keeps
        the state related to MSG_PROPOSE
        --- add the new ResponseCollector to the outstanding propose set
        --- create MSG_PROPOSE: message carries the corresponding ballotnumber, commandnumber and the proposal
        --- broadcast MSG_PROPOSE to the same Acceptor nodes from the PREPARE STAGE
        """
        if self.outstandingprepares.has_key(msg.inresponseto):
            prc = self.outstandingprepares[msg.inresponseto]
            print "[%s] got an accept for ballotno %s commandno %s proposal %s with %d out of %d" % (self, prc.ballotnumber, prc.commandnumber, prc.proposal, prc.nresponses, prc.ntotal)
            prc.nresponses += 1
            if msg.ballotnumber > prc.ballotnumber:
                print "!!!!!!!!!!!!!!!!! prc ballotnumber error, should not happen"

            prc.naccepts += 1
            # collect all the p-values from responses that have the same commandnumber as me
            if msg.pvalueset is not None:
                for pvalue in msg.pvalueset.pvalues:
                    if pvalue.commandnumber == prc.commandnumber:
                        prc.possiblepvalueset.add(pvalue)

            print prc.nresponses, prc.nquorum
            if prc.naccepts >= prc.nquorum:
                print "[%s] suffiently many accepts on prepare" % (self,)
                # choose a p-value out of the set encountered and collected so far
                chosenpvalue = prc.possiblepvalueset.pickMaxBallotNumber()
                # take the old response collector out of the outstanding prepare set
                del self.outstandingprepares[msg.inresponseto]
                # create a new response collector for the PROPOSE
                newprc = ResponseCollector(prc.acceptors, prc.ballotnumber, prc.commandnumber, prc.proposal)
                # add the new response collector to the outstanding propose set
                self.outstandingproposes[prc.ballotnumber] = newprc
                # create and send PROPOSE message
                propose = PaxosMessage(MSG_PROPOSE,self.me,prc.ballotnumber,commandnumber=chosenpvalue.commandnumber,proposal=chosenpvalue.proposal)
                prc.acceptors.broadcast(self, propose)
        else:
            print "[%s] there is no response collector" % (self,)

    def msg_prepare_reject(self, conn, msg):
        """Handler for MSG_PREPARE_REJECT
        MSG_PREPARE_REJECT is handled only if it belongs to an outstanding MSG_PREPARE,
        otherwise it is discarded.
        A MSG_PREPARE_REJECT causes the PREPARE STAGE to be unsuccessful, hence the current
        state is deleted and a ne PREPARE STAGE is initialized.

        State Updates:
        - kill the PREPARE STAGE that received a MSG_PREPARE_REJECT
        -- remove the old ResponseCollector from the outstanding prepare set
        - increment the ballotnumber
        - call doCommand() to start a new PREPARE STAGE:
        """
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
        """Handler for MSG_PROPOSE_ACCEPT
        MSG_PROPOSE_ACCEPT is handled only if it belongs to an outstanding MSG_PREPARE,
        otherwise it is discarded.
        When MSG_PROPOSE_ACCEPT is received, the corresponding ResponseCollector is retrieved
        and its state is updated accordingly.

        State Updates:
        - nresponses and naccepts are incremented
        - if naccepts is greater than the quorum size, PROPOSE STAGE is successful.
        -- increment the ballotnumber (for use in the next PREPARE STAGE)
        -- remove the old ResponseCollector from the outstanding prepare set
        -- create MSG_PERFORM: message carries the chosen commandnumber and proposal.
        -- broadcast MSG_PERFORM to all Replicas
        """
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
        """Handler for MSG_PROPOSE_REJECT
        MSG_PROPOSE_REJECT is handled only if it belongs to an outstanding MSG_PROPOSE,
        otherwise it is discarded.
        A MSG_PROPOSE_REJECT causes the PROPOSE STAGE to be unsuccessful, hence the current
        state is deleted and a new PREPARE STAGE is initialized.

        State Updates:
        - kill the PROPOSE STAGE that received a MSG_PROPOSE_REJECT
        -- remove the old ResponseCollector from the outstanding prepare set
        - increment the ballotnumber
        - call doCommand() to start a new PREPARE STAGE:
        """
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
        """Shell command [command]: Initiate a new command.
        This function calls doCommand() with inputs from the Shell.""" 
        commandnumber = args[1]
        proposal = ' '.join(args[2:])
        self.doCommand(int(commandnumber), proposal)
                    
def main():
    theLeader = Leader()
    theLeader.startservice()

if __name__=='__main__':
    main()
