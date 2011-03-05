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
        - pendingcommands: Set of unissiued commands that are waiting for the window to roll over to be issued
        """
        Node.__init__(self, NODE_REPLICA)
        self.object = replicatedobject
        self.nexttoexecute = 1
        self.decisions = {}
        self.proposals = {}
        self.pendingcommands = {}

    def performcore(self, msg, slotno, dometaonly=False):
        print "---> SlotNo: %d Command: %s DoMetaOnly: %s" % (slotno, self.decisions[slotno], dometaonly)
        command = self.decisions[slotno][COMMAND]
        commandlist = command.command.split()
        commandname = commandlist[0]
        commandargs = commandlist[1:]
        ismeta=(commandname in METACOMMANDS)
        try:
            if dometaonly and ismeta:
                # execute a metacommand when the window has expired
                method = getattr(self, commandname)
                givenresult = method(commandargs)
            elif dometaonly and not ismeta:
                return
            elif not dometaonly and ismeta:
                # meta command, but the window has not passed yet, 
                # so just mark it as executed without actually executing it
                # the real execution will take place when the window has expired
                tempcommand = (CMD_EXECUTED,self.decisions[slotno][COMMAND])
                self.decisions[slotno] = tempcommand
                return
            elif not dometaonly and not ismeta:
                # this is the workhorse case that executes most normal commands
                method = getattr(self.object, commandname)
                givenresult = method(commandargs)
        except AttributeError:
            print "command not supported: %s" % (command)
            givenresult = 'COMMAND NOT SUPPORTED'
        cmdstatus, cmd = self.decisions[slotno]
        self.decisions[slotno] = (CMD_EXECUTED, cmd, givenresult)
        if commandname not in METACOMMANDS:
            # if this client contacted me for this operation, return him the response 
            if self.type == NODE_LEADER and command.client.id() in self.clientpool.poolbypeer.keys():
                clientreply = ClientMessage(MSG_CLIENTREPLY,self.me,givenresult, command.clientcommandnumber)
                clientconn = self.clientpool.get_connection_by_peer(command.client)
                clientconn.send(clientreply)

    def perform(self, msg):
        """Function to handle local perform operations. 
        """
        if not self.decisions.has_key(msg.commandnumber):
            self.decisions[msg.commandnumber] = (CMD_DECIDED,msg.proposal)
        if self.proposals.has_key(msg.commandnumber) and self.decisions[msg.commandnumber][1] != self.proposals[msg.commandnumber]:
            self.do_command_propose(self.proposals[msg.commandnumber])

        while self.decisions.has_key(self.nexttoexecute) and self.decisions[self.nexttoexecute][COMMANDSTATE] != CMD_EXECUTED:
            logger("Executing command %d." % self.nexttoexecute)
            
            # check to see if there was a meta command precisely WINDOW commands ago that should now take effect
            if self.nexttoexecute > WINDOW:
                self.performcore(msg, self.nexttoexecute - WINDOW, True)

            self.performcore(msg, self.nexttoexecute)
            self.nexttoexecute += 1
            # the window just got bumped by one
            # check if there are pending commands, and issue one of them
            self.issue_pending_command(self.nexttoexecute)
            
    def issue_pending_command(self, candidatecommandno):
        if self.pendingcommands.has_key(candidatecommandno):
            self.do_command_propose_frompending(candidatecommandno)

    def msg_perform(self, conn, msg):
        """Handler for MSG_PERFORM"""
        self.perform(msg)

    def add_acceptor(self, args):
        # args keep addr:port
        args = args[0].split(":")
        acceptor = Peer(args[0],int(args[1]),NODE_ACCEPTOR)
        self.groups[NODE_ACCEPTOR].add(acceptor)
        
    def del_acceptor(self, args):
        args = args[0].split(":")
        acceptor = Peer(args[0],int(args[1]),NODE_REPLICA)
        self.groups[NODE_ACCEPTOR].remove(acceptor)
    
    def add_replica(self, args):
        args = args[0].split(":")
        replica = Peer(args[0],int(args[1]),NODE_REPLICA)
        self.groups[NODE_REPLICA].add(replica)
        
    def del_replica(self, args):
        args = args[0].split(":")
        replica = Peer(args[0],int(args[1]),NODE_REPLICA)
        self.groups[NODE_REPLICA].remove(replica)

    def cmd_showobject(self, args):
        """Shell command [showobject]: Print Replicated Object information""" 
        print self.object

    def cmd_info(self, args):
        """Shell command [info]: Print Requests and Command to execute next"""
        print "Waiting to execute #%d" % self.nexttoexecute
        print "Decisions:\n"
        for (commandnumber,command) in self.decisions.iteritems():
            print "%d:\t%s\t%s\t%s\n" %  (commandnumber, command[COMMAND], command[COMMANDRESULT], cmd_states[command[COMMANDSTATE]])

# LEADER STATE
    def become_leader(self):
        """Initialize Leader

        Leader State
        - active: indicates if the Leader has a *good* ballotnumber
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
            self.active = False
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
        """Returns the first gap in the proposals dictionary or the item following """
        commandgap = 1
        proposals = set(self.proposals.keys() + self.decisions.keys() + self.pendingcommands.keys())
        while commandgap <= len(proposals):
            if commandgap in proposals:
                commandgap += 1
            else:
                return commandgap
        return commandgap

    def handle_client_command(self, givencommand):
        if self.type != NODE_LEADER:
            print "Not a Leader.."
            return
        
        if self.receivedclientrequests.has_key((givencommand.client,givencommand.clientcommandnumber)):
            logger("client request received before")
            resultsent = False
            # Check if the request has been executed
            for (commandnumber,command) in self.decisions.iteritems():
                if command[COMMAND] == givencommand:
                    clientreply = ClientMessage(MSG_CLIENTREPLY,self.me,command[COMMANDRESULT],givencommand.clientcommandnumber)
                    conn = self.get_connection_by_peer(givencommand.client)
                    if conn is not None:
                        conn.send(clientreply)
                    resultsent = True
                    break
            # If request not executed yet, send REQUEST IN PROGRESS
            if not resultsent:
                clientreply = ClientMessage(MSG_CLIENTREPLY,self.me,"REQUEST IN PROGRESS",givencommand.clientcommandnumber)
                conn = self.get_connection_by_peer(givencommand.client)
                if conn is not None:
                    conn.send(clientreply)    
        else:
            self.receivedclientrequests[(givencommand.client,givencommand.clientcommandnumber)] = givencommand
            logger("Initiating a New Command")
            logger("Leader is active: %s" % self.active)
            proposal = givencommand
            if self.active:
                self.do_command_propose(proposal)
            else:
                self.do_command_prepare(proposal)

    def msg_clientrequest(self, conn, msg):
        """Handler for a MSG_CLIENTREQUEST
        A new Paxos Protocol is initiated with the first available commandnumber
        the Leader knows of.
        """
        self.check_leader_promotion()
        if self.type != NODE_LEADER:
            logger("Not a Leader.. Request rejected..")
            clientreply = ClientMessage(MSG_CLIENTREPLY,self.me,"REJECTED",msg.command.clientcommandnumber)
            conn.send(clientreply)
            return
        
        self.clientpool.add_connection_to_peer(msg.source, conn)
        self.handle_client_command(msg.command)

    def msg_clientreply(self, conn, msg):
        """This only occurs in response to commands initiated by the shell"""
        print "==================>", msg

    def msg_response(self, conn, msg):
        """Handler for MSG_RESPONSE"""
        logger("Received response from Replica")
        clientreply = ClientMessage(MSG_CLIENTREPLY,self.me,msg.result)
        # self.send(clientreply,peer=CLIENT) # XXX

    def do_command_propose_frompending(self, givencommandnumber):
        givenproposal = self.pendingcommands[givencommandnumber]
        self.proposals[givencommandnumber] = givenproposal
        del self.pendingcommands[givencommandnumber]
        recentballotnumber = self.ballotnumber
        logger("2 proposing command: %d:%s" % (givencommandnumber,givenproposal))
        logger("with ballotnumber %s" % str(recentballotnumber))
        logger("and %d acceptors" % len(self.groups[NODE_ACCEPTOR]))
        prc = ResponseCollector(self.groups[NODE_ACCEPTOR], recentballotnumber, givencommandnumber, givenproposal)
        self.outstandingproposes[givencommandnumber] = prc
        propose = PaxosMessage(MSG_PROPOSE,self.me,recentballotnumber,commandnumber=givencommandnumber,proposal=givenproposal)
        self.send(propose,group=prc.acceptors)
        
    # Paxos Methods
    def do_command_propose(self, givenproposal):
        """Propose a command with the given commandnumber and proposal. Stage p2a.
        A command is proposed by running the PROPOSE stage of Paxos Protocol for the command.
        """
        if self.type != NODE_LEADER:
            print "Not a Leader.."
            return

        givencommandnumber = self.find_commandnumber()
        self.pendingcommands[givencommandnumber] = givenproposal
        # if we're too far in the future, i.e. past window, do not issue the command
        if givencommandnumber - self.nexttoexecute >= WINDOW:
            return
        self.do_command_propose_frompending(givencommandnumber)
            
    def do_command_prepare_frompending(self, givencommandnumber):
        givenproposal = self.pendingcommands[givencommandnumber]
        self.proposals[givencommandnumber] = givenproposal
        del self.pendingcommands[givencommandnumber]
        newballotnumber = self.ballotnumber
        logger("1 preparing command: %d:%s" % (givencommandnumber, givenproposal))
        logger("with ballotnumber %s" % str(newballotnumber))
        prc = ResponseCollector(self.groups[NODE_ACCEPTOR], newballotnumber, givencommandnumber, givenproposal)
        self.outstandingprepares[newballotnumber] = prc
        prepare = PaxosMessage(MSG_PREPARE,self.me,newballotnumber)
        self.send(prepare,group=prc.acceptors)

    def do_command_prepare(self, givenproposal):
        """Prepare a command with the given commandnumber and proposal. Stage p1a.
        A command is initiated by running a Paxos Protocol for the command.

        State Updates:
        - Start from the PREPARE STAGE:
        -- create MSG_PREPARE: message carries the corresponding ballotnumber
        -- create ResponseCollector object for PREPARE STAGE: ResponseCollector keeps
        the state related to MSG_PREPARE
        -- add the ResponseCollector to the outstanding prepare set
        -- send MSG_PREPARE to Acceptor nodes
        """
        if self.type != NODE_LEADER:
            print "Not a Leader.."
            return

        givencommandnumber = self.find_commandnumber()
        self.pendingcommands[givencommandnumber] = givenproposal
        # if we're too far in the future, i.e. past window, do not issue the command
        if givencommandnumber - self.nexttoexecute >= WINDOW:
            return
        self.do_command_prepare_frompending(givencommandnumber)
            
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
                del self.outstandingprepares[msg.inresponseto]
                # choose pvalues with distinctive commandnumbers and highest ballotnumbers
                pmaxset = prc.possiblepvalueset.pmax()
                for commandnumber,proposal in pmaxset.iteritems():
                    self.proposals[commandnumber] = proposal
                # If the commandnumber we were planning to use is overwritten
                # we should try proposing with a new commandnumber
                if self.proposals[prc.commandnumber] != prc.proposal:
                    self.do_command_propose(prc.proposal)
                # PROPOSE for each proposal in proposals
                for chosencommandnumber,chosenproposal in self.proposals.iteritems():
                    print "Sending PROPOSE for %d, %s" % (chosencommandnumber, chosenproposal)
                    newprc = ResponseCollector(prc.acceptors, prc.ballotnumber, chosencommandnumber, chosenproposal)
                    self.outstandingproposes[chosencommandnumber] = newprc
                    propose = PaxosMessage(MSG_PROPOSE,self.me,prc.ballotnumber,commandnumber=chosencommandnumber,proposal=chosenproposal)
                    self.send(propose,group=newprc.acceptors)
                # become active
                self.active = True
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
            # become inactive
            self.active = False
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
            prc.received[msg.source] = msg
            logger("got an accept for proposal ballotno %s commandno %s proposal %s making %d out of %d accepts" % (prc.ballotnumber, prc.commandnumber, prc.proposal, len(prc.received), prc.ntotal))
            assert msg.ballotnumber == prc.ballotnumber, "[%s] MSG_PROPOSE_ACCEPT can't have non-matching ballotnumber" % self
            if len(prc.received) >= prc.nquorum:
                logger("WE AGREE!")
                # take this response collector out of the outstanding propose set
                self.proposals[prc.commandnumber] = prc.proposal
                del self.outstandingproposes[msg.commandnumber]
                # now we can perform this action on the replicas
                performmessage = PaxosMessage(MSG_PERFORM,self.me,commandnumber=prc.commandnumber,proposal=prc.proposal)
                self.send(performmessage, group=self.groups[NODE_REPLICA])
                self.send(performmessage, group=self.groups[NODE_LEADER])
                self.perform(performmessage)
        else:
            logger("there is no response collector for %s cmdno:%d" % (str(msg.inresponseto), msg.commandnumber))

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
            logger("got a reject for proposal ballotno %s commandno %s proposal %s still %d out of %d accepts" % (prc.ballotnumber, prc.commandnumber, prc.proposal, len(prc.received), prc.ntotal))
            # take this response collector out of the outstanding propose set
            del self.outstandingproposes[msg.commandnumber]
            # become inactive
            self.active = False
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
            cmdproposal = Command(client=self.me, clientcommandnumber=random.randint(1,10000000), command=proposal)
            self.handle_client_command(cmdproposal)
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
