'''
@author: denizalti
@note: The Replica keeps an object and responds to Perform messages received from the Leader.
@date: February 1, 2011
'''
from threading import Thread, Lock, Condition
import time
import random
import math

from node import Node
from enums import *
from connection import Connection, ConnectionPool
from group import Group
from peer import Peer
from message import Message, PaxosMessage, HandshakeMessage, AckMessage, PValue, PValueSet, ClientMessage
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

class Replica(Node):
    """Replica receives MSG_PERFORM from Leaders and execute corresponding commands."""
    def __init__(self, replicatedobject):
        """Initialize Replica

        Replica State
        - object: the object that Replica is replicating
        - nexttodecide: the commandnumber that should be used for the next proposal
	- nexttoexecute: the commandnumber that relica is waiting for to execute
        - requests: received requests as <commandnumber:(commandstate,command|result)> mappings
		       - 'commandstate' can be CMD_EXECUTED, CMD_DECIDED, CMD_RUNNING
                       		-- CMD_EXECUTED: The command corresponding to the commandnumber has 
                                		 been both decided and executed.
				-- CMD_DECIDED: The command corresponding to the commandnumber has 
                                		 been decided but it is not executed yet (probably due to an 
						 outstanding command prior to this command.)
				-- CMD_RUNNING: The commandnumber is assigned to a command but the 
					         result is not known yet.
        """
        Node.__init__(self, NODE_REPLICA)
        self.object = replicatedobject
        self.nexttodecide = 1
        self.nexttoexecute = 1
        self.requests = {}

    def msg_perform(self, conn, msg):
        """Handler for MSG_PERFORM

        Upon receiving MSG_PERFORM Replica updates its state as follows:
        - Add the command to the requests dictionary if it's not already there
        - Execute the command (and any consecutive command in requests)
        if it has the commandnumber matching nexttoexecute
              -- call the corresponding method from the replicated object
              -- update requests: with the new state and result (commandstate,result)
              -- create MSG_RESPONSE: message carries the commandnumber and the result of the command
              -- send MSG_RESPONSE to Leader
              -- increment nexttoexecute
        """
        if not self.requests.has_key(msg.commandnumber):
            self.requests[msg.commandnumber] = (CMD_DECIDED,msg.proposal)
                         
        while self.requests.has_key(self.nexttoexecute) and self.requests[self.nexttoexecute][COMMANDSTATE] != CMD_EXECUTED:
            print "[%s] Executing command %d." % (self, self.nexttoexecute)
            command = self.requests[self.nexttoexecute][COMMAND] # magic number 
            commandlist = command.split()
            commandname = commandlist[0]
            commandargs = commandlist[1:]
            try:
                method = getattr(self.object, commandname)
            except AttributeError:
                print "command not supported: %s" % (command)
                givenresult = 'COMMAND NOT SUPPORTED'
            givenresult = method(commandargs)
            self.requests[self.nexttoexecute] = (CMD_EXECUTED,givenresult)
            replymsg = PaxosMessage(MSG_RESPONSE,self.me,commandnumber=self.nexttoexecute,result=givenresult)
            self.send(replymsg,peer=msg.source)
            self.nexttoexecute += 1

    def perform(self, msg):
        """Function to handle local perform operations. Used if the replica is also a leader.

        The state is updated as follows:
        - Add the command to the requests dictionary if it's not already there
        - Execute the command (and any consecutive command in requests)
        if it has the commandnumber matching nexttoexecute
              -- call the corresponding method from the replicated object
              -- update requests: with the new state and result (commandstate,result)
              -- increment nexttoexecute
        """
        if not self.requests.has_key(msg.commandnumber):
            self.requests[msg.commandnumber] = (CMD_DECIDED,msg.proposal)
                         
        while self.requests.has_key(self.nexttoexecute) and self.requests[self.nexttoexecute][COMMANDSTATE] != CMD_EXECUTED:
            print "[%s] Executing command %d." % (self, self.nexttoexecute)
            command = self.requests[self.nexttoexecute][COMMAND] # magic number 
            commandlist = command.split()
            commandname = commandlist[0]
            commandargs = commandlist[1:]
            try:
                method = getattr(self.object, commandname)
            except AttributeError:
                print "command not supported: %s" % (command)
                givenresult = 'COMMAND NOT SUPPORTED'
            givenresult = method(commandargs)
            self.requests[self.nexttoexecute] = (CMD_EXECUTED,givenresult)
            self.nexttoexecute += 1

    def cmd_showobject(self, args):
        """Shell command [showobject]: Print Replicated Object information""" 
        print self.object

    def cmd_info(self, args):
        """Shell command [info]: Print Requests and Command to execute next"""
        print "Waiting for command #%d" % self.nexttoexecute
        print "Completed Requests:\n"
        for (commandnumber,command) in self.requests.iteritems():
            print "%d:\t%s\t%s\n" %  (commandnumber, command[COMMAND], cmd_states[command[COMMANDSTATE]])

# LEADER STATE
    def become_leader(self):
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
        self.type = NODE_LEADER
        self.ballotnumber = (0,self.id)
        self.proposals = {}
        self.outstandingprepares = {}
        self.outstandingproposes = {}
        self.receivedclientrequests = {} # indexed by (clientid,clientcommandnumber)
        self.clientconnections = {}

    def update_ballotnumber(self,seedballotnumber):
        """Update the ballotnumber with a higher value than given ballotnumber"""
        temp = (seedballotnumber[0]+1,self.ballotnumber[1])
        self.ballotnumber = temp
        
    def get_highest_commandnumber(self):
        """Return the highest Commandnumber the Leader knows of."""
        temp = self.nexttodecide
        self.nexttodecide += 1
        return temp

    def msg_clientrequest(self, conn, msg):
        """Handler for a MSG_CLIENTREQUEST
        A new Paxos Protocol is initiated with the first available commandnumber
        the Leader knows of.
        """
        try:
            if self.receivedclientrequests.has_key((msg.command.clientid,msg.command.clientcommandnumber)):
                print "[%s] Client Request handled before.. Request discarded.." % self
            else:
                self.clientconnections[msg.source.id()] = conn
                self.receivedclientrequests[(msg.command.clientid,msg.command.clientcommandnumber)] = msg.command.command
                print "[%s] Initiating a New Command" % self
                commandnumber = self.get_highest_commandnumber()
                proposal = msg.command.command
            self.do_command(commandnumber, proposal)
        except AttributeError:
            print "[%s] Not a Leader.. Request rejected.." % self
            clientreply = ClientMessage(MSG_CLIENTREPLY,self.me,"REJECTED")
            self.send(clientreply,peer=msg.source)

    def msg_response(self, conn, msg):
        """Handler for MSG_RESPONSE"""
        print "[%s] Received response from Replica" % self
        clientreply = ClientMessage(MSG_CLIENTREPLY,self.me,msg.result)
        # self.send(clientreply,peer=CLIENT) # XXX

     # Paxos Methods
    def do_command(self, commandnumber, proposal):
        """Do a command with the given commandnumber and proposal.
        A command is initiated by running a Paxos Protocol for the command.

        State Updates:
        - Start the PREPARE STAGE:
        -- create MSG_PREPARE: message carries the corresponding ballotnumber Then a new
        -- create ResponseCollector object for PREPARE STAGE: ResponseCollector keeps
        the state related to MSG_PREPARE
        -- add the ResponseCollector to the outstanding prepare set
        -- send MSG_PREPARE to Acceptor nodes
        """
        recentballotnumber = self.ballotnumber
        print "[%s] initiating command: %d:%s" % (self,commandnumber,proposal)
        print "[%s] with ballotnumber %s" % (self,str(recentballotnumber))
        prepare = PaxosMessage(MSG_PREPARE,self.me,recentballotnumber)
        prc = ResponseCollector(self.groups[NODE_ACCEPTOR], recentballotnumber, commandnumber, proposal)
        self.outstandingprepares[recentballotnumber] = prc
        self.send(prepare, group=prc.acceptors)

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
        --- update own proposals dictionary according to pmax dictionary
        --- remove the old ResponseCollector from the outstanding prepare set
        --- run the PROPOSE STAGE for each pvalue in proposals dictionary
        ---- create ResponseCollector object for PROPOSE STAGE: ResponseCollector keeps
        the state related to MSG_PROPOSE
        ---- add the new ResponseCollector to the outstanding propose set
        ---- create MSG_PROPOSE: message carries the corresponding ballotnumber, commandnumber and the proposal
        ---- send MSG_PROPOSE to the same Acceptor nodes from the PREPARE STAGE
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
                print "[%s] suffiently many accepts on prepare" % self
                # choose pvalues with distinctive commandnumbers and highest ballotnumbers
                pmaxset = prc.possiblepvalueset.pmax()
                for commandnumber,proposal in pmaxset.iteritems():
                    self.proposals[commandnumber] = proposal
                del self.outstandingprepares[msg.inresponseto]
                # PROPOSE for each proposal in proposals
                for chosencommandnumber,chosenproposal in self.proposals.iteritems():
                    newprc = ResponseCollector(prc.acceptors, prc.ballotnumber, chosencommandnumber, chosenproposal)
                    self.outstandingproposes[chosencommandnumber] = newprc
                    propose = PaxosMessage(MSG_PROPOSE,self.me,prc.ballotnumber,commandnumber=chosencommandnumber,proposal=chosenproposal)
                    self.send(propose,group=newprc.acceptors)
        else:
            print "[%s] there is no response collector" % self

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
        - call do_command() to start a new PREPARE STAGE:
        """
        if self.outstandingprepares.has_key(msg.inresponseto):
            prc = self.outstandingprepares[msg.inresponseto]
            print "[%s] got a reject for ballotno %s commandno %s proposal %s with %d out of %d" % (self, prc.ballotnumber, prc.commandnumber, prc.proposal, len(prc.received), prc.ntotal)
            # take this response collector out of the outstanding prepare set
            del self.outstandingprepares[msg.inresponseto]
            # update the ballot number
            self.update_ballotnumber(msg.ballotnumber)
            # retry the prepare
            self.do_command(prc.commandnumber, prc.proposal)
        else:
            print "[%s] there is no response collector" % self

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
        -- send MSG_PERFORM to all Replicas and Leaders
        -- execute the command
        """
        if self.outstandingproposes.has_key(msg.commandnumber):
            prc = self.outstandingproposes[msg.commandnumber]
            print "[%s] got an accept for proposal ballotno %s commandno %s proposal %s with %d out of %d" % (self, prc.ballotnumber, prc.commandnumber, prc.proposal, len(prc.received), prc.ntotal)
            prc.received[msg.source] = msg
            assert msg.ballotnumber == prc.ballotnumber, "[%s] MSG_PROPOSE_ACCEPT can't have non-matching ballotnumber" % self
            if len(prc.received) >= prc.nquorum:
                # YAY, WE AGREE!
                self.update_ballotnumber(self.ballotnumber)
                # take this response collector out of the outstanding propose set
                del self.outstandingproposes[msg.commandnumber]
                # now we can perform this action on the replicas
                performmessage = PaxosMessage(MSG_PERFORM,self.me,commandnumber=prc.commandnumber,proposal=prc.proposal)
                self.send(performmessage, group=self.groups[NODE_REPLICA])
                self.send(performmessage, group=self.groups[NODE_LEADER])
                self.perform(performmessage)
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
        - call do_command() to start a new PREPARE STAGE:
        """
        if self.outstandingproposes.has_key(msg.commandnumber):
            prc = self.outstandingproposes[msg.commandnumber]
            print "[%s] got a reject for proposal ballotno %s commandno %s proposal %s with %d out of %d" % (self, prc.ballotnumber, prc.commandnumber, prc.proposal, len(prc.received), prc.ntotal)
            # take this response collector out of the outstanding propose set
            del self.outstandingproposes[msg.commandnumber]
            # update the ballot number
            self.update_ballotnumber(msg.ballotnumber)
            # retry the prepare
            self.do_command(prc.commandnumber, prc.proposal)
        else:
            print "[%s] there is no response collector for %s" % (self,str(msg.inresponseto))

    # Debug Methods
    def cmd_command(self, args):
        """Shell command [command]: Initiate a new command.
        This function calls do_command() with inputs from the Shell.""" 
        commandnumber = args[1]
        proposal = ' '.join(args[2:])
        self.do_command(int(commandnumber), proposal)

    def cmd_goleader(self, args):
        """Shell command [goleader]: Start Leader state""" 
        self.become_leader()

    def cmd_clients(self,args):
        """Prints Client Connections"""
        for id, conn in self.clientconnections.iteritems():
            print id, "  :  ", conn

def main():
    theReplica = Replica(Test())
    theReplica.startservice()

if __name__=='__main__':
    main()
