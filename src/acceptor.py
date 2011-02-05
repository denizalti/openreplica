'''
@author: denizalti
@note: The Acceptor acts like a server, responds to PaxosMessages received from the leader.
@date: February 1, 2011
'''
from threading import Thread
from random import randint
import threading

from enums import *
from node import Node
from connection import ConnectionPool
from group import Group
from peer import Peer
from message import Message,PaxosMessage,HandshakeMessage,PValue,PValueSet

class Acceptor(Node):
    def __init__(self):
        Node.__init__(self, NODE_ACCEPTOR)

        # Synod Acceptor State
        self.ballotnumber = (0,0)
        self.accepted = PValueSet()
        
    def msg_prepare(self, conn, msg):
        if msg.ballotnumber > self.ballotnumber:
            print "[%s] prepare received with acceptable ballotnumber %s", (self, str(msg.ballotnumber))
            self.ballotnumber = msg.ballotnumber
            replymsg = PaxosMessage(MSG_ACCEPT,self.me,self.ballotnumber,givenpvalueset=self.accepted)
        else:
            print "[%s] prepare received with non-acceptable ballotnumber %s", (self, str(msg.ballotnumber))
            replymsg = PaxosMessage(MSG_REJECT,self.me,self.ballotnumber,givenpvalueset=self.accepted)
        conn.send(replymsg)

    def msg_propose(self, conn, msg):
        if msg.ballotnumber >= self.ballotnumber:
            print "[%s] propose received with acceptable ballotnumber %s", (self, str(msg.ballotnumber))
            self.ballotnumber = msg.ballotnumber
            newpvalue = PValue(msg.ballotnumber,msg.commandnumber,msg.proposal)
            self.accepted.add(newpvalue)
            replymsg = PaxosMessage(MSG_ACCEPT,self.me,self.ballotnumber,newpvalue.commandnumber)
        else:
            print "[%s] propose received with non-acceptable ballotnumber %s", (self, str(msg.ballotnumber))
            replymsg = PaxosMessage(MSG_REJECT,self.me,self.ballotnumber,newpvalue.commandnumber)
        conn.send(replymsg)

    def cmd_paxos(self, args):
        print self.accepted
        
def main():
    theAcceptor = Acceptor()
    theAcceptor.startservice()

if __name__=='__main__':
    main()

  


    
