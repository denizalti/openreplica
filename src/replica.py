'''
@author: denizalti
@note: The Replica keeps an object and responds to Perform messages received from the Leader.
@date: February 1, 2011
'''
from threading import Thread, Lock, Condition
import time

from node import Node
from enums import *
from connection import Connection,ConnectionPool
from group import Group
from peer import Peer
from message import Message,PaxosMessage,HandshakeMessage,AckMessage,PValue,PValueSet
from test import Test
from bank import Bank

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
    def become_leader():
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
        if self.receivedclientrequests.has_key((msg.command.clientid,msg.command.clientcommandnumber)):
            print "[%s] Client Request handled before.. Request discarded.." % self
        else:
            self.receivedclientrequests[(msg.command.clientid,msg.command.clientcommandnumber)] = msg.command.command
            print "[%s] Initiating a New Command" % self
            commandnumber = self.get_highest_commandnumber()
            proposal = msg.command.command
            self.do_command(commandnumber, proposal)

    def msg_response(self, conn, msg):
        """Handler for MSG_RESPONSE"""
        print "[%s] Received response from Replica" % self
        clientreply = ClientMessage(MSG_CLIENTREPLY,self.me,msg.result)
        self.send(clientreply,peer=msg.source)

def main():
    theReplica = Replica(Test())
    theReplica.startservice()

if __name__=='__main__':
    main()
