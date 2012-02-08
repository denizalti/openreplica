"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: The Acceptor keeps track of past Paxos ballots. It is the log for the Paxos state.
@date: February 1, 2011
@copyright: See COPYING.txt
"""
from threading import Thread
import signal
from enums import *
from utils import *
from node import *
from connection import ConnectionPool
from group import Group
from peer import Peer
from message import Message, PaxosMessage, GarbageCollectMessage
from pvalue import PValue, PValueSet

class Acceptor(Node):
    """Acceptor keeps track of past Paxos ballots. It supports garbage collection by keeping track
    of an object snapshot and trimming all previous ballots prior to the snapshot.
    """
    def __init__(self):
        """
        - ballotnumber: the highest ballotnumber Acceptor has encountered
        - accepted: all pvalues Acceptor has accepted thus far
        """
        Node.__init__(self, NODE_ACCEPTOR)
        self.ballotnumber = (0,0)
        self.last_accept_msg_id = -1
        self.accepted = PValueSet()
        self.objectsnapshot = (0,None)
        
    def msg_prepare(self, conn, msg):
        """
        MSG_PREPARE is accepted only if it carries a ballotnumber greater
        than the highest ballotnumber Acceptor has ever received.

        Replies:
        - MSG_PREPARE_ADOPTED carries the ballotnumber that is received and all pvalues
        accepted thus far.
        - MSG_PREPARE_PREEMPTED carries the highest ballotnumber Acceptor has seen and all
        pvalues accepted thus far.
        """
        # this ballot should be strictly higher than previous ballots we have accepted,
        if msg.ballotnumber > self.ballotnumber:
            self.logger.write("Paxos State", "prepare received with acceptable ballotnumber %s" % str(msg.ballotnumber))
            self.ballotnumber = msg.ballotnumber
            self.last_accept_msg_id = msg.fullid()
            replymsg = PaxosMessage(MSG_PREPARE_ADOPTED,self.me,ballotnumber=self.ballotnumber,inresponsetoballotnumber=msg.ballotnumber,givenpvalueset=self.accepted)
        # or else it should be a precise duplicate of the last request, in which case we do nothing
        elif msg.ballotnumber == self.ballotnumber and msg.fullid() == self.last_accept_msg_id:
            return
        else:
            self.logger.write("Paxos State", "prepare received with non-acceptable ballotnumber %s for commandnumber %s" % (str(msg.ballotnumber), str(msg.commandnumber)))
            replymsg = PaxosMessage(MSG_PREPARE_PREEMPTED,self.me,ballotnumber=self.ballotnumber,inresponsetoballotnumber=msg.ballotnumber,givenpvalueset=self.accepted)
        self.logger.write("Paxos State", "prepare responding with %s" % str(replymsg))
        self.send(replymsg,peer=msg.source)

    def msg_propose(self, conn, msg):
        """
        MSG_PROPOSE is accepted only if it carries a ballotnumber greater
        than the highest ballotnumber Acceptor has received.

        Replies:
        - MSG_PROPOSE_ACCEPT carries the ballotnumber and the commandnumber that are received.
        - MSG_PROPOSE_REJECT carries the highest ballotnumber Acceptor has seen and the
        commandnumber that is received.
        """
        if msg.ballotnumber >= self.ballotnumber:
            self.logger.write("Paxos State", "propose received with acceptable ballotnumber %s" % str(msg.ballotnumber))
            self.ballotnumber = msg.ballotnumber
            newpvalue = PValue(msg.ballotnumber,msg.commandnumber,msg.proposal)
            self.accepted.add(newpvalue)
            replymsg = PaxosMessage(MSG_PROPOSE_ACCEPT,self.me,ballotnumber=self.ballotnumber,inresponsetoballotnumber=msg.ballotnumber,commandnumber=msg.commandnumber)
        else:
            self.logger.write("Paxos State", "propose received with non-acceptable ballotnumber %s" % str(msg.ballotnumber))
            replymsg = PaxosMessage(MSG_PROPOSE_REJECT,self.me,ballotnumber=self.ballotnumber,inresponsetoballotnumber=msg.ballotnumber,commandnumber=msg.commandnumber)
        self.send(replymsg,peer=msg.source)

    def msg_garbagecollect(self, conn, msg):
        self.logger.write("Paxos State", "Doing garbage collection upto %d" % msg.commandnumber)
        success = self.accepted.truncateto(msg.commandnumber)
        if success:
            self.objectsnapshot = (msg.commandnumber,msg.snapshot)
        else:
            self.logger.write("Garbage Collection Error", "Garbege Collection failed.")
        
    def cmd_paxos(self, args):
        """Shell command [paxos]: Print the paxos state of the Acceptor."""
        keytuples = self.accepted.pvalues.keys()
        print sorted(keytuples, key=lambda keytuple: keytuple[0])
        
def main():
    acceptornode = Acceptor().startservice()
    signal.signal(signal.SIGINT, acceptornode.terminate_handler)
    signal.signal(signal.SIGTERM, acceptornode.terminate_handler)
    signal.pause()

if __name__=='__main__':
    main()
