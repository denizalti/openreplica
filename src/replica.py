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
        
    def msg_perform(self, conn, msg):
        self.requests[msg.commandnumber] = msg.proposal
        command = msg.proposal.split()
        commandname = command[0]
        commandargs = command[1:]
        try:
            method = getattr(self.object, commandname)
            method(commandargs)
        except AttributeError:
            print "command not supported: %s" % (command)
    
    def cmd_showobject(self, args):
        print self.object

def main():
    theReplica = Replica(Test())
    theReplica.startservice()

if __name__=='__main__':
    main()

  


    
