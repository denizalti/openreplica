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
        self.object = replicatedobject
        
    def msg_perform(self, msg):
        self.state[message.commandnumber] = message.proposal
        command = msg.proposal.split()
        commandname = command[0]
        commandargs = command[1:]
        try:
            method = getattr(self, commandname)
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

  


    
