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
        self.accepted = PValueSet()
        
    def msg_prepare(self, conn, msg):
        if msg.ballotnumber > self.ballotnumber:
            print "ACCEPTOR got a PREPARE with Ballotnumber: ", msg.ballotnumber
            print "ACCEPTOR's Ballotnumber: ", self.ballotnumber
            self.ballotnumber = msg.ballotnumber
            replymsg = PaxosMessage(MSG_ACCEPT,self.me,self.ballotnumber,givenpvalueset=self.accepted)
        else:
            replymsg = PaxosMessage(MSG_REJECT,self.me,self.ballotnumber,givenpvalueset=self.accepted)
        conn.send(replymsg)

    def msg_propose(self, conn, msg):
        if msg.ballotnumber >= self.ballotnumber:
            self.ballotnumber = msg.ballotnumber
            newpvalue = PValue(msg.ballotnumber,msg.commandnumber,msg.proposal)
            self.accepted.add(newpvalue)
            replymsg = PaxosMessage(MSG_ACCEPT,self.me,self.ballotnumber,newpvalue.commandnumber)
        else:
            replymsg = PaxosMessage(MSG_REJECT,self.me,self.ballotnumber,newpvalue.commandnumber)
        conn.send(replymsg)

    def cmd_paxos(self, args):
        print self.accepted
        
def main():
    theAcceptor = Acceptor()
    theAcceptor.startservice()

if __name__=='__main__':
    main()

  


    
