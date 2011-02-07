'''
@author: denizalti
@note: The Replica keeps an object and responds to Perform messages received from the Leader.
@date: February 1, 2011
'''
from threading import Thread, Lock, Condition

from node import Node
from enums import *
from utils import *
from connection import Connection,ConnectionPool
from group import Group
from peer import Peer
from message import Message,PaxosMessage,HandshakeMessage,PValue,PValueSet
from test import Test
from bank import Bank

class Replica(Node):
    """Replica receives MSG_PERFORM from Leaders and execute corresponding commands."""
    def __init__(self, replicatedobject):
        """Initialize Replica

        Replica State
        - object: the object that Replica is replicating
        - commandnumber: the highest commandnumber Replica knows about
        - requests: received requests indexed by commandnumbers
        """
        Node.__init__(self, NODE_REPLICA)
        self.object = replicatedobject  # this is the state
        self.commandnumber = 1  # incremented upon performing an operation
        self.requests = {}

    def msg_perform(self, conn, msg):
        """Handler for MSG_PERFORM

        Upon receiving MSG_PERFORM Replica updates its state and executes the
        command in the request.
        - Add the request to the requests dictionary
        - Execute the command in the request on the replicated object
        - create MSG_RESPONSE: message carries the commandnumber and the result of the command
        - send MSG_RESPONSE to Leader
        """
        self.requests[msg.commandnumber] = msg.proposal
        command = msg.proposal.split()
        commandname = command[0]
        commandargs = command[1:]
        try:
            method = getattr(self.object, commandname)
            givenresult = method(commandargs)
        except AttributeError:
            print "command not supported: %s" % (command)
            replymsg = PaxosMessage(MSG_RESPONSE,self.me,commandnumber=msg.commandnumber,result="FAIL")
            conn.send(replymsg)
            return
        replymsg = PaxosMessage(MSG_RESPONSE,self.me,commandnumber=msg.commandnumber,result=givenresult)
        conn.send(replymsg)
    
    def cmd_showobject(self, args):
        """Shell command [showobject]: Print Replicated Object information""" 
        print self.object

def main():
    theReplica = Replica(Test())
    theReplica.startservice()

if __name__=='__main__':
    main()
