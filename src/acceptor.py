'''
@author: denizalti
@note: The Acceptor acts like a server.
'''
from threading import Thread
from random import randint
import threading

from node import Node
from enums import *
from utils import *
from communicationutils import *
from connection import *
from group import *
from peer import *
from message import *

class Acceptor(Node):
    def __init__(self):
        Node.__init__(self, NODE_ACCEPTOR)

        # Synod Acceptor State
        self.ballotnumber = (0,0)
        self.accepted = [] # Array of pvalues
        
    def msg_prepare(self, msg):
        if msg.ballotnumber > self.ballotnumber:
            print "ACCEPTOR got a PREPARE with Ballotnumber: ", msg.ballotnumber
            print "ACCEPTOR's Ballotnumber: ", self.ballotnumber
            self.ballotnumber = msg.ballotnumber
            replymsg = PaxosMessage(MSG_ACCEPT,self.me,self.ballotnumber,givenpvalues=self.accepted)
        else:
            replymsg = PaxosMessage(MSG_REJECT,self.me,self.ballotnumber,givenpvalues=self.accepted)
        connection.send(replymsg)

    def msg_propose(self, msg):
        if msg.ballotnumber >= self.ballotnumber:
            self.ballotnumber = msg.ballotnumber
            newpvalue = PValue(ballotnumber=msg.ballotnumber,commandnumber=msg.commandnumber,proposal=msg.proposal)
            self.accepted.append(newpvalue)
            replymsg = Message(type=MSG_ACCEPT,source=self.toPeer.serialize(),ballotnumber=self.ballotnumber,commandnumber=newpvalue.commandnumber)
        else:
            replymsg = Message(type=MSG_REJECT,source=self.toPeer.serialize(),ballotnumber=self.ballotnumber,commandnumber=newpvalue.commandnumber)
        connection.send(replymsg)

    def cmd_paxos(self, args):
        for accepted in self.accepted:
            print accepted
        
def main():
    theAcceptor = Acceptor()
    theAcceptor.startservice()

if __name__=='__main__':
    main()

  


    
