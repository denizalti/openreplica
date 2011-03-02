'''
@author: denizalti
@note: The Replica keeps an object and responds to Perform messages received from the Leader.
@date: February 1, 2011
'''
from threading import Thread, Lock, Condition
import operator
import time
import random
import math

from node import Node
from enums import *
from utils import *
from connection import Connection, ConnectionPool
from group import Group
from peer import Peer
from message import Message, PaxosMessage, HandshakeMessage, AckMessage, PValue, PValueSet, ClientMessage, Command
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

class Replica(Node):
    """Replica receives MSG_PERFORM from Leaders and execute corresponding commands."""
    def __init__(self, replicatedobject):
        """Initialize Replica

        Replica State
        - object: the object that Replica is replicating
	- nexttoexecute: the commandnumber that relica is waiting for to execute
        - decisions: received requests as <commandnumber:(commandstate,command,commandresult)> mappings
		       - 'commandstate' can be CMD_EXECUTED, CMD_DECIDED
                       		-- CMD_EXECUTED: The command corresponding to the commandnumber has 
                                		 been both decided and executed.
				-- CMD_DECIDED: The command corresponding to the commandnumber has 
                                		 been decided but it is not executed yet (probably due to an 
						 outstanding command prior to this command.)
        - outstandingproposals: <commandnumber:command> mappings that the replica has made in the past
        """
        Node.__init__(self, NODE_REPLICA)
        self.object = replicatedobject
        self.nexttoexecute = 1
        self.decisions = {}
        self.proposals = {}

    def performcore(self, msg, slotno, dometaonly=False):
        print "------------- CHECKING %d ----> %s" % (slotno, self.decisions[slotno])
        command = self.decisions[slotno][COMMAND]
        commandlist = command.command.split()
        commandname = commandlist[0]
        commandargs = commandlist[1:]
        try:
            if commandname in METACOMMANDS:
                if dometaonly:
                    method = getattr(self, commandname)
                else:
                    self.decisions[slotno] = (CMD_EXECUTED,'')
                    return
            else:
                if dometaonly:
                    return
                else:
                    method = getattr(self.object, commandname)
        except AttributeError:
            print "command not supported: %s" % (command)
            givenresult = 'COMMAND NOT SUPPORTED'
        givenresult = method(commandargs)
        cmdstatus, cmd = self.decisions[slotno]
        self.decisions[slotno] = (CMD_EXECUTED, cmd, givenresult)
        if commandname not in METACOMMANDS:
            # if this client contacted me for this operation, return him the response 
            if self.type == NODE_LEADER and command.client.id() in self.clientpool.poolbypeer.keys():
                clientreply = ClientMessage(MSG_CLIENTREPLY,self.me,givenresult, command.clientcommandnumber)
                clientconn = self.clientpool.get_connection_by_peer(command.client)
                clientconn.send(clientreply)
            else:
                # i am a replica that was contacted by a leader, return the response to him
                # XXX not clear if this is necessary
                replymsg = PaxosMessage(MSG_RESPONSE,self.me,commandnumber=self.nexttoexecute,result=givenresult)
                self.send(replymsg,peer=msg.source)

    def perform(self, msg):
        """Function to handle local perform operations. 
        """
        if not self.decisions.has_key(msg.commandnumber):
            self.decisions[msg.commandnumber] = (CMD_DECIDED,msg.proposal)
        if self.proposals.has_key(msg.commandnumber) and self.decisions[msg.commandnumber][1] != self.proposals[msg.commandnumber]:
            print "--> This shouldn't happen as we should have caught this during PMAX"
            self.do_command_propose(self.proposals[msg.commandnumber])

        while self.decisions.has_key(self.nexttoexecute) and self.decisions[self.nexttoexecute][COMMANDSTATE] != CMD_EXECUTED:
            logger("Executing command %d." % self.nexttoexecute)
            
            # check to see if there was a meta command precisely WINDOW commands ago that should now take effect
            if self.nexttoexecute > WINDOW:
                self.performcore(msg, self.nexttoexecute - WINDOW, True)

            self.performcore(msg, self.nexttoexecute)
            self.nexttoexecute += 1

    def msg_perform(self, conn, msg):
        """Handler for MSG_PERFORM"""
        self.perform(msg)

    def add_acceptor(self, args):
        pass
    def del_acceptor(self, args):
        pass
    def add_replica(self, args):
        pass
    def del_replica(self, args):
        pass

    def cmd_showobject(self, args):
        """Shell command [showobject]: Print Replicated Object information""" 
        print self.object

    def cmd_info(self, args):
        """Shell command [info]: Print Requests and Command to execute next"""
        print "Waiting to execute #%d" % self.nexttoexecute
        print "Decisions:\n"
        for (commandnumber,command) in self.decisions.iteritems():
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
        if self.type != NODE_LEADER:
            self.type = NODE_LEADER
            self.ballotnumber = (0,self.id)
            self.outstandingprepares = {}
            self.outstandingproposes = {}
            self.receivedclientrequests = {} # indexed by (client,clientcommandnumber)
            self.clientpool = ConnectionPool()
            
    def unbecome_leader(self):
        """Stop being a leader"""
        # fail-stop tolerance, coupled with retries in the client, mean that a 
        # leader can at any time discard all of its internal state and the protocol
        # will still work correctly.
        self.type = NODE_REPLICA

    def check_leader_promotion(self):
        minpeer = None
        for peer in self.groups[NODE_LEADER]:
            if minpeer is None or peer < minpeer:
                minpeer = peer
        for peer in self.groups[NODE_REPLICA]:
            if minpeer is None or peer < minpeer:
                minpeer = peer
        if minpeer is None or self.me < minpeer:
            # i need to step up and become a leader
            if self.type != NODE_LEADER:
                logger("Becoming a Leader")
                self.become_leader()
        elif self.type == NODE_LEADER:
            # there is someone else who should act as a leader
            logger("Unbecoming a Leader")
            self.unbecome_leader()

    def update_ballotnumber(self,seedballotnumber):
        """Update the ballotnumber with a higher value than given ballotnumber"""
        temp = (seedballotnumber[0]+1,self.ballotnumber[1])
        self.ballotnumber = temp

    def find_commandnumber(self):
        """Returns the first gap in the proposals dictionary"""
        commandgap = 1
        proposals = dict(self.proposals.items() + self.decisions.items())
        sorted_by_commandnumbers = sorted(proposals.iteritems(), key=operator.itemgetter(0))
        for commandnumber,proposal in sorted_by_commandnumbers:
            if commandgap == commandnumber:
                commandgap = commandnumber+1
        return commandgap
    
    def msg_clientrequest(self, conn, msg):
        """Handler for a MSG_CLIENTREQUEST
        A new Paxos Protocol is initiated with the first available commandnumber
        the Leader knows of.
        """
        self.check_leader_promotion()
        if self.type == NODE_LEADER:
            if self.receivedclientrequests.has_key((msg.command.client,msg.command.clientcommandnumber)):
                logger("Client Request handled before.. Resending result..")
                for (commandnumber,command) in self.decisions.iteritems():
                    if command[COMMAND] == msg.command:
                        clientreply = ClientMessage(MSG_CLIENTREPLY,self.me,command[COMMANDRESULT],msg.command.clientcommandnumber)
                        conn.send(clientreply)
            else:
                self.clientpool.add_connection_to_peer(msg.source, conn)
                self.receivedclientrequests[(msg.command.client,msg.command.clientcommandnumber)] = msg.command
                logger("Initiating a New Command")
                proposal = msg.command
                self.do_command_propose(proposal)
        else:
            logger("Not a Leader.. Request rejected..")
            clientreply = ClientMessage(MSG_CLIENTREPLY,self.me,"REJECTED",msg.command.clientcommandnumber)
            conn.send(clientreply)

    def msg_response(self, conn, msg):
        """Handler for MSG_RESPONSE"""
        logger("Received response from Replica")
        clientreply = ClientMessage(MSG_CLIENTREPLY,self.me,msg.result)
        # self.send(clientreply,peer=CLIENT) # XXX

    # Paxos Methods
    def do_command_propose(self, givenproposal):
        """Propose a command with the given commandnumber and proposal.
        A command is proposed by running the PROPOSE stage of Paxos Protocol for the command.

        State Updates:
        - Start the PROPOSE STAGE:
        -- create MSG_PROPOSE: message carries the corresponding ballotnumber, commandnumber and proposal
        -- create ResponseCollector object for PROPOSE STAGE: ResponseCollector keeps
        the state related to MSG_PROPOSE
        -- add the ResponseCollector to the outstanding propose set
        -- send MSG_PROPOSE to Acceptor nodes
        """
        if self.type == NODE_LEADER:
            recentballotnumber = self.ballotnumber
            givencommandnumber = self.find_commandnumber()
            logger("proposing command: %d:%s" % (givencommandnumber,givenproposal))
            logger("with ballotnumber %s" % str(recentballotnumber))
            prc = ResponseCollector(self.groups[NODE_ACCEPTOR], recentballotnumber, givencommandnumber, givenproposal)
            self.outstandingproposes[givencommandnumber] = prc
            propose = PaxosMessage(MSG_PROPOSE,self.me,recentballotnumber,commandnumber=givencommandnumber,proposal=givenproposal)
            self.send(propose,group=prc.acceptors)
        else:
            print "Not a Leader.."

    def do_command_prepare(self, givenproposal):
        """Prepare a command with the given commandnumber and proposal.
        A command is initiated by running a Paxos Protocol for the command.

        State Updates:
        - Start from the PREPARE STAGE:
        -- create MSG_PREPARE: message carries the corresponding ballotnumber
        -- create ResponseCollector object for PREPARE STAGE: ResponseCollector keeps
        the state related to MSG_PREPARE
        -- add the ResponseCollector to the outstanding prepare set
        -- send MSG_PREPARE to Acceptor nodes
        """
        if self.type == NODE_LEADER:
            newballotnumber = self.ballotnumber
            givencommandnumber = self.find_commandnumber()
            logger("preparing command: %d:%s" % (givencommandnumber, givenproposal))
            logger("with ballotnumber %s" % str(newballotnumber))
            prc = ResponseCollector(self.groups[NODE_ACCEPTOR], newballotnumber, givencommandnumber, givenproposal)
            self.outstandingprepares[newballotnumber] = prc
            prepare = PaxosMessage(MSG_PREPARE,self.me,newballotnumber)
            self.send(prepare,group=prc.acceptors)
        else:
            print "Not a Leader.."
            
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
            prc = self.outstandingprepares[msg.inresponseto]
            prc.received[msg.source] = msg
            logger("got an accept for ballotno %s commandno %s proposal %s with %d out of %d" % (prc.ballotnumber, prc.commandnumber, prc.proposal, len(prc.received), prc.ntotal))
            assert msg.ballotnumber == prc.ballotnumber, "[%s] MSG_PREPARE_ADOPTED can't have non-matching ballotnumber" % self
            # collect all the p-values from the response
            if msg.pvalueset is not None:
                for pvalue in msg.pvalueset.pvalues:
                    prc.possiblepvalueset.add(pvalue)

            if len(prc.received) >= prc.nquorum:
                logger("suffiently many accepts on prepare!")
                # choose pvalues with distinctive commandnumbers and highest ballotnumbers
                pmaxset = prc.possiblepvalueset.pmax()
                for commandnumber,proposal in pmaxset.iteritems():
                    self.proposals[commandnumber] = proposal
                # If the commandnumber we were planning to use is in the proposals
                # we should try the next one
                self.do_command_propose(prc.proposal)
                del self.outstandingprepares[msg.inresponseto]
                # PROPOSE for each proposal in proposals
                for chosencommandnumber,chosenproposal in self.proposals.iteritems():
                    print "Sending PROPOSE for %d, %s" % (chosencommandnumber, chosenproposal)
                    newprc = ResponseCollector(prc.acceptors, prc.ballotnumber, chosencommandnumber, chosenproposal)
                    self.outstandingproposes[chosencommandnumber] = newprc
                    propose = PaxosMessage(MSG_PROPOSE,self.me,prc.ballotnumber,commandnumber=chosencommandnumber,proposal=chosenproposal)
                    self.send(propose,group=newprc.acceptors)
        else:
            logger("there is no response collector")

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
        - call do_command_prepare() to start a new PREPARE STAGE:
        """
        if self.outstandingprepares.has_key(msg.inresponseto):
            prc = self.outstandingprepares[msg.inresponseto]
            logger("got a reject for ballotno %s commandno %s proposal %s with %d out of %d" % (prc.ballotnumber, prc.commandnumber, prc.proposal, len(prc.received), prc.ntotal))
            # take this response collector out of the outstanding prepare set
            del self.outstandingprepares[msg.inresponseto]
            # update the ballot number
            self.update_ballotnumber(msg.ballotnumber)
            # retry the prepare
            self.do_command_prepare(prc.proposal)
        else:
            logger("there is no response collector")

    def msg_propose_accept(self, conn, msg):
        """Handler for MSG_PROPOSE_ACCEPT
        MSG_PROPOSE_ACCEPT is handled only if it belongs to an outstanding MSG_PREPARE,
        otherwise it is discarded.
        When MSG_PROPOSE_ACCEPT is received, the corresponding ResponseCollector is retrieved
        and its state is updated accordingly.

        State Updates:
        - message is added to the received dictionary
        - if length of received is greater than the quorum size, PROPOSE STAGE is successful.
        -- remove the old ResponseCollector from the outstanding prepare set
        -- create MSG_PERFORM: message carries the chosen commandnumber and proposal.
        -- send MSG_PERFORM to all Replicas and Leaders
        -- execute the command
        """
        if self.outstandingproposes.has_key(msg.commandnumber):
            prc = self.outstandingproposes[msg.commandnumber]
            logger("got an accept for proposal ballotno %s commandno %s proposal %s with %d out of %d" % (prc.ballotnumber, prc.commandnumber, prc.proposal, len(prc.received), prc.ntotal))
            prc.received[msg.source] = msg
            assert msg.ballotnumber == prc.ballotnumber, "[%s] MSG_PROPOSE_ACCEPT can't have non-matching ballotnumber" % self
            if len(prc.received) >= prc.nquorum:
                # YAY, WE AGREE!
                # take this response collector out of the outstanding propose set
                self.proposals[prc.commandnumber] = prc.proposal
                del self.outstandingproposes[msg.commandnumber]
                # now we can perform this action on the replicas
                performmessage = PaxosMessage(MSG_PERFORM,self.me,commandnumber=prc.commandnumber,proposal=prc.proposal)
                self.send(performmessage, group=self.groups[NODE_REPLICA])
                self.send(performmessage, group=self.groups[NODE_LEADER])
                self.perform(performmessage)
        else:
            logger("there is no response collector for %s" % str(msg.inresponseto))

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
        - call do_command_prepare() to start a new PREPARE STAGE:
        """
        if self.outstandingproposes.has_key(msg.commandnumber):
            prc = self.outstandingproposes[msg.commandnumber]
            logger("got a reject for proposal ballotno %s commandno %s proposal %s with %d out of %d" % (prc.ballotnumber, prc.commandnumber, prc.proposal, len(prc.received), prc.ntotal))
            # take this response collector out of the outstanding propose set
            del self.outstandingproposes[msg.commandnumber]
            # update the ballot number
            self.update_ballotnumber(msg.ballotnumber)
            # retry the prepare
            self.do_command_prepare(prc.proposal)
        else:
            logger("there is no response collector for %s" % str(msg.inresponseto))

    # Debug Methods
    def cmd_command(self, args):
        """Shell command [command]: Initiate a new command.
        This function calls do_command_propose() with inputs from the Shell."""
        try:
            proposal = ' '.join(args[1:])
            cmdproposal = Command(client='Test', command=proposal)
            self.do_command_propose(cmdproposal)
        except IndexError:
            print "command expects only one command"

    def cmd_goleader(self, args):
        """Shell command [goleader]: Start Leader state""" 
        self.become_leader()

    def cmd_clients(self,args):
        """Prints Client Connections"""
        print self.clientpool

def main():
    theReplica = Replica(Bank())
    theReplica.startservice()

if __name__=='__main__':
    main()
