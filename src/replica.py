'''
@author: denizalti
@note: The Leader
'''
from threading import Thread, Lock, Condition

from node import Node
from enums import *
from utils import *
from communicationutils import *
from connection import Connection
from group import Group
from peer import Peer
from message import Message

from test import Test

class Replica(Node):
    def __init__(self, replicatedobject):
        Node.__init__(self, NODE_REPLICA)
        self.object = replicatedobject  # this is the state
        self.commandnumber = 1  # incremented upon performing an operation
        self.requests = {}

    # TODO: According to the paper the replica gets the Client identifier and sends the response to the Client
    # Wouldn't this cause multiple responses to the Client?
    def msg_perform(self, conn, msg):
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
        print self.object

def main():
    theReplica = Replica(Test())
    theReplica.startservice()

if __name__=='__main__':
    main()

  


    
