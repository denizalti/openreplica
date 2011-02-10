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
from replica import Replica
from enums import *
from connection import ConnectionPool
from group import Group
from peer import Peer
from message import ClientMessage,Message,PaxosMessage,HandshakeMessage,AckMessage,PValue,PValueSet

from test import Test
from bank import Bank

# Class used to collect responses to both PREPARE and PROPOSE messages
class ResponseCollector():
    """ResponseCollector keeps the state related to both MSG_PREPARE and
    MSG_PROPOSE.
    """
    def __init__(self, acceptors, ballotnumber, commandnumber, proposal):
        """Initialize ResponseCollector

        ResponseCollector State
        - ballotnumber: ballotnumber for the corresponding MSG
        - commandnumber: commandnumber for the corresponding MSG
        - proposal: proposal for the corresponding MSG
        - acceptors: Group of Acceptor nodes for the corresponding MSG
        - received: dictionary that keeps <peer:reply> mappings
        - ntotal: # Acceptor nodes for the corresponding MSG
        - nquorum: # ACCEPTs needed for success
        - possiblepvalueset: Set of pvalues collected from Acceptors
        """
        self.ballotnumber = ballotnumber
        self.commandnumber = commandnumber
        self.proposal = proposal
        self.acceptors = acceptors
        self.received = {}
        self.ntotal = len(self.acceptors)
        self.nquorum = min(math.ceil(float(self.ntotal)/2+1), self.ntotal)
        self.possiblepvalueset = PValueSet()
        self.possiblepvalueset.add(PValue(self.ballotnumber, self.commandnumber, self.proposal))

class Leader(Node,Replica):
    """Leader extends a Node and keeps additional state about the Paxos Protocol and Commands in progress."""
    def __init__(self):
        """Initialize Leader

        Leader State
        - ballotnumber: the highest ballotnumber Leader has used
        - pvalueset: the PValueSet for Leader, which encloses all
        (ballotnumber,commandnumber,proposal) triples Leader knows about
        - object: the object that Leader is replicating (as it is a Replica too)
        - commandnumber: the highest commandnumber Leader knows about
        - outstandingprepares: ResponseCollector dictionary for MSG_PREPARE,
        indexed by ballotnumber
        - outstandingproposes: ResponseCollector dictionary for MSG_PROPOSE,
        indexed by ballotnumber
        """
        Node.__init__(self, NODE_LEADER)
        
        self.ballotnumber = (0,self.id)
        self.pvalueset = PValueSet()
        # YYY self.commandnumber = 1  # incremented upon performing an operation
        self.outstandingprepares = {}
        self.outstandingproposes = {}

    def updateBallotnumber(self,seedballotnumber):
        """Update the ballotnumber with a higher value than given ballotnumber"""
        temp = (seedballotnumber[0]+1,self.ballotnumber[1])
        self.ballotnumber = temp
        
    def getHighestCommandNumber(self):
        """Return the highest Commandnumber the Leader knows of."""
        return max(k for k, v in self.requests.iteritems() if v != 0) if len(self.requests) > 0 else 1
        
    def msg_clientrequest(self, conn, msg):
        """Handler for a MSG_CLIENTREQUEST
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

    def msg_response(self, conn, msg):
        """Handler for MSG_RESPONSE"""
        print "[%s] Received response from Replica" % (self,)
        print msg.result

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
        recentballotnumber = self.ballotnumber
        print "[%s] initiating command: %d:%s" % (self,commandnumber,proposal)
        print "[%s] with ballotnumber %s" % (self,str(recentballotnumber))
        prepare = PaxosMessage(MSG_PREPARE,self.me,recentballotnumber)
        prc = ResponseCollector(self.groups[NODE_ACCEPTOR], recentballotnumber, commandnumber, proposal)
        self.outstandingprepares[recentballotnumber] = prc
        prc.acceptors.broadcast(self, prepare)

    def msg_prepare_adopted(self, conn, msg):
        """Handler for MSG_PREPARE_ADOPTED
        MSG_PREPARE_ADOPTED is handled only if it belongs to an outstanding MSG_PREPARE,
        otherwise it is discarded.
        When MSG_PREPARE_ADOPTED is received, the corresponding ResponseCollector is retrieved
        and its state is updated accordingly.

        State Updates:
        - message is added to the received dictionary
        - the pvalue with the ResponseCollector's commandnumber is added to the possiblepvalueset
        - if naccepts is greater than the quorum size PREPARE STAGE is successful.
        -- Start the PROPOSE STAGE:
        --- create the pvalueset with highest ballotnumbers for distinctive commandnumbers
        --- remove the old ResponseCollector from the outstanding prepare set
        --- run the PROPOSE STAGE for each pvalue in the above pvalueset
        ---- create ResponseCollector object for PROPOSE STAGE: ResponseCollector keeps
        the state related to MSG_PROPOSE
        ---- add the new ResponseCollector to the outstanding propose set
        ---- create MSG_PROPOSE: message carries the corresponding ballotnumber, commandnumber and the proposal
        ---- broadcast MSG_PROPOSE to the same Acceptor nodes from the PREPARE STAGE
        """
        if self.outstandingprepares.has_key(msg.inresponseto):
            print "Found the key for the outstandingprepare %s" %str(msg.inresponseto)
            prc = self.outstandingprepares[msg.inresponseto]
            prc.received[msg.source] = msg
            print "[%s] got an accept for ballotno %s commandno %s proposal %s with %d out of %d" % (self, prc.ballotnumber, prc.commandnumber, prc.proposal, len(prc.received), prc.ntotal)
            assert msg.ballotnumber == prc.ballotnumber, "[%s] MSG_PREPARE_ADOPTED can't have non-matching ballotnumber" % self
            # collect all the p-values from the response
            if msg.pvalueset is not None:
                for pvalue in msg.pvalueset.pvalues:
                    prc.possiblepvalueset.add(pvalue)

            if len(prc.received) >= prc.nquorum:
                print "[%s] suffiently many accepts on prepare" % (self,)
                # choose pvalues with distinctive commandnumbers and highest ballotnumbers
                # out of the set encountered and collected so far
                pmaxset = prc.possiblepvalueset.pMax()
                # YYY 
                # take the old response collector out of the outstanding prepare set
                del self.outstandingprepares[msg.inresponseto]
                for (pmaxcommandnumber,pmaxproposal) in pmaxset.iteritems():
                    # create a new response collector for the PROPOSE
                    newprc = ResponseCollector(prc.acceptors, prc.ballotnumber, prc.commandnumber, prc.proposal)
                    # add the new response collector to the outstanding propose set
                    self.outstandingproposes[pmaxcommandnumber] = newprc
                    # create and send PROPOSE message
                    propose = PaxosMessage(MSG_PROPOSE,self.me,prc.ballotnumber,commandnumber=pmaxcommandnumber,proposal=pmaxproposal)
                    newprc.acceptors.broadcast(self, propose)
        else:
            print "[%s] there is no response collector" % (self,)

    def msg_prepare_preempted(self, conn, msg):
        """Handler for MSG_PREPARE_PREEMPTED
        MSG_PREPARE_PREEMPTED is handled only if it belongs to an outstanding MSG_PREPARE,
        otherwise it is discarded.
        A MSG_PREPARE_PREEMPTED causes the PREPARE STAGE to be unsuccessful, hence the current
        state is deleted and a ne PREPARE STAGE is initialized.

        State Updates:
        - kill the PREPARE STAGE that received a MSG_PREPARE_PREEMPTED
        -- remove the old ResponseCollector from the outstanding prepare set
        - update the ballotnumber
        - call doCommand() to start a new PREPARE STAGE:
        """
        if self.outstandingprepares.has_key(msg.inresponseto):
            prc = self.outstandingprepares[msg.inresponseto]
            print "[%s] got a reject for ballotno %s commandno %s proposal %s with %d out of %d" % (self, prc.ballotnumber, prc.commandnumber, prc.proposal, len(prc.received), prc.ntotal)
            # take this response collector out of the outstanding prepare set
            del self.outstandingprepares[msg.inresponseto]
            # update the ballot number
            self.updateBallotnumber(msg.ballotnumber)
            # retry the prepare
            self.doCommand(prc.commandnumber, prc.proposal)
        else:
            print "[%s] there is no response collector" % (self,)

    def msg_propose_accept(self, conn, msg):
        """Handler for MSG_PROPOSE_ACCEPT
        MSG_PROPOSE_ACCEPT is handled only if it belongs to an outstanding MSG_PREPARE,
        otherwise it is discarded.
        When MSG_PROPOSE_ACCEPT is received, the corresponding ResponseCollector is retrieved
        and its state is updated accordingly.

        State Updates:
        - message is added to the received dictionary
        - if length of received is greater than the quorum size, PROPOSE STAGE is successful.
        -- update the ballotnumber (for use in the next PREPARE STAGE)
        -- remove the old ResponseCollector from the outstanding prepare set
        -- create MSG_PERFORM: message carries the chosen commandnumber and proposal.
        -- broadcast MSG_PERFORM to all Replicas and Leaders
        -- execute the command
        """
        if self.outstandingproposes.has_key(msg.commandnumber):
            prc = self.outstandingproposes[msg.commandnumber]
            print "[%s] got an accept for proposal ballotno %s commandno %s proposal %s with %d out of %d" % (self, prc.ballotnumber, prc.commandnumber, prc.proposal, len(prc.received), prc.ntotal)
            prc.received[msg.source] = msg
            assert msg.ballotnumber == prc.ballotnumber, "[%s] MSG_PROPOSE_ACCEPT can't have non-matching ballotnumber" % self
            if len(prc.received) >= prc.nquorum:
                # YAY, WE AGREE!
                self.updateBallotnumber(self.ballotnumber)
                # take this response collector out of the outstanding propose set
                del self.outstandingproposes[msg.commandnumber]
                # now we can perform this action on the replicas
                perform = PaxosMessage(MSG_PERFORM,self.me,commandnumber=prc.commandnumber,proposal=prc.proposal)
                self.groups[NODE_REPLICA].broadcast(self, perform)
                self.groups[NODE_LEADER].broadcast(self, perform)
        else:
            print "[%s] there is no response collector for %s" % (self,str(msg.inresponseto))

    def msg_propose_reject(self, conn, msg):
        """Handler for MSG_PROPOSE_REJECT
        MSG_PROPOSE_REJECT is handled only if it belongs to an outstanding MSG_PROPOSE,
        otherwise it is discarded.
        A MSG_PROPOSE_REJECT causes the PROPOSE STAGE to be unsuccessful, hence the current
        state is deleted and a new PREPARE STAGE is initialized.

        State Updates:
        - kill the PROPOSE STAGE that received a MSG_PROPOSE_REJECT
        -- remove the old ResponseCollector from the outstanding prepare set
        - update the ballotnumber
        - call doCommand() to start a new PREPARE STAGE:
        """
        if self.outstandingproposes.has_key(msg.commandnumber):
            prc = self.outstandingproposes[msg.commandnumber]
            print "[%s] got a reject for proposal ballotno %s commandno %s proposal %s with %d out of %d" % (self, prc.ballotnumber, prc.commandnumber, prc.proposal, len(prc.received), prc.ntotal)
            # take this response collector out of the outstanding propose set
            del self.outstandingproposes[msg.commandnumber]
            # update the ballot number
            self.updateBallotnumber(msg.ballotnumber)
            # retry the prepare
            self.doCommand(prc.commandnumber, prc.proposal)
        else:
            print "[%s] there is no response collector for %s" % (self,str(msg.inresponseto))

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
