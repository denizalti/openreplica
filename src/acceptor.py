"""
@author: denizalti
@note: The Acceptor
@date: February 1, 2011
"""
from threading import Thread
from random import randint

from enums import *
from utils import *
from node import Node
from connection import ConnectionPool
from group import Group
from peer import Peer
from message import Message,PaxosMessage,HandshakeMessage,AckMessage,PValue,PValueSet

class Acceptor(Node):
    """Acceptor acts like a server responding to PaxosMessages received from the Leader.
    It extends a Node and keeps additional state about the Paxos Protocol.
    """
    def __init__(self):
        """Initialize Acceptor

        Acceptor State
        - ballotnumber: the highest ballotnumber Acceptor has encountered
        - accepted: all pvalues Acceptor has accepted thus far
        """
        Node.__init__(self, NODE_ACCEPTOR)
        self.ballotnumber = (0,0)
        self.accepted = PValueSet()
        
    def msg_prepare(self, conn, msg):
        """Handler for MSG_PREPARE.
        MSG_PREPARE is accepted only if it carries a ballotnumber greater
        than the highest ballotnumber Acceptor has ever received.

        Replies:
        - MSG_PREPARE_ADOPTED carries the ballotnumber that is received and all pvalues
        accepted thus far.
        - MSG_PREPARE_PREEMPTED carries the highest ballotnumber Acceptor has seen and all
        pvalues accepted thus far.
        """
        if msg.ballotnumber > self.ballotnumber:
            logger("prepare received with acceptable ballotnumber %s" % str(msg.ballotnumber))
            self.ballotnumber = msg.ballotnumber
            replymsg = PaxosMessage(MSG_PREPARE_ADOPTED,self.me,self.ballotnumber,msg.ballotnumber,givenpvalueset=self.accepted)
        else:
            logger("prepare received with non-acceptable ballotnumber %s" % str(msg.ballotnumber))
            replymsg = PaxosMessage(MSG_PREPARE_PREEMPTED,self.me,self.ballotnumber,msg.ballotnumber,givenpvalueset=self.accepted)
        logger("prepare responding to ballotnumber %s" % str(msg.ballotnumber))
        self.send(replymsg,peer=msg.source)

    def msg_propose(self, conn, msg):
        """Handler for MSG_PROPOSE.
        MSG_PROPOSE is accepted only if it carries a ballotnumber greater
        than the highest ballotnumber Acceptor has received.

        Replies:
        - MSG_PROPOSE_ACCEPT carries the ballotnumber and the commandnumber that are received.
        - MSG_PROPOSE_REJECT carries the highest ballotnumber Acceptor has seen and the
        commandnumber that is received.
        """
        if msg.ballotnumber >= self.ballotnumber:
            logger("propose received with acceptable ballotnumber %s" % str(msg.ballotnumber))
            self.ballotnumber = msg.ballotnumber
            newpvalue = PValue(msg.ballotnumber,msg.commandnumber,msg.proposal)
            self.accepted.add(newpvalue)
            replymsg = PaxosMessage(MSG_PROPOSE_ACCEPT,self.me,self.ballotnumber,msg.ballotnumber,newpvalue.commandnumber)
        else:
            logger("propose received with non-acceptable ballotnumber %s" % str(msg.ballotnumber))
            replymsg = PaxosMessage(MSG_PROPOSE_REJECT,self.me,self.ballotnumber,msg.ballotnumber,newpvalue.commandnumber)
        self.send(replymsg,peer=msg.source)

    def cmd_paxos(self, args):
        """Shell command [paxos]: Print the paxos state of the Acceptor.""" 
        print self.accepted
        
def main():
    theAcceptor = Acceptor()
    theAcceptor.startservice()

if __name__=='__main__':
    main()

  


    
