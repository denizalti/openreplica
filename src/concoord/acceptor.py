"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: The Acceptor keeps track of past Paxos ballots. It is the log for the Paxos state.
@copyright: See LICENSE
"""
import signal
from threading import Thread
from concoord.node import *
from concoord.enums import *
from concoord.utils import *
from concoord.peer import Peer
from concoord.group import Group
from concoord.pvalue import PValue, PValueSet
from concoord.connection import ConnectionPool
from concoord.message import Message, PaxosMessage, GarbageCollectMessage
from concoordprofiler import *

class Acceptor(Node):
    """
    Acceptor keeps track of past Paxos ballots. It supports garbage
    collection by keeping track of an object snapshot and trimming all
    previous ballots prior to the snapshot.
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
        if self.debug:
            profile_on() # Turn profiling on!
        
    def msg_prepare(self, conn, msg):
        """
        MSG_PREPARE is accepted only if it carries a ballotnumber greater
        than the highest ballotnumber Acceptor has ever received.

        Replies:
        - MSG_PREPARE_ADOPTED carries the ballotnumber that is received and 
        all pvalues accepted thus far.
        - MSG_PREPARE_PREEMPTED carries the highest ballotnumber Acceptor
        has seen and all pvalues accepted thus far.
        """
        # this ballot should be strictly higher than previously accepted ballots
        if msg.ballotnumber >= self.ballotnumber:
            self.logger.write("Paxos State",
                              "prepare received with acceptable ballotnumber %s"
                              % str(msg.ballotnumber))

            self.ballotnumber = msg.ballotnumber
            self.last_accept_msg_id = msg.fullid()
            replymsg = PaxosMessage(MSG_PREPARE_ADOPTED,
                                    self.me,ballotnumber=self.ballotnumber,
                                    inresponsetoballotnumber=msg.ballotnumber,
                                    givenpvalueset=self.accepted)
                                    #XXX The accepted set grows, messages become larger
                                    #The garbage collection should be used more efficiently
        # or else it should be a precise duplicate of the last request
        # in this case we do nothing
        elif msg.ballotnumber == self.ballotnumber and \
                msg.fullid() == self.last_accept_msg_id:
            return
        else:
            self.logger.write("Paxos State",
                              ("prepare received with non-acceptable "
                               "ballotnumber %s "
                               "for commandnumber %s") % (str(msg.ballotnumber),
                                                          str(msg.commandnumber)))

            replymsg = PaxosMessage(MSG_PREPARE_PREEMPTED,
                                    self.me,ballotnumber=self.ballotnumber,
                                    inresponsetoballotnumber=msg.ballotnumber,
                                    givenpvalueset=self.accepted)

        self.logger.write("Paxos State", "prepare responding with %s"
                          % str(replymsg))
        self.send(replymsg,peer=msg.source)

    def msg_propose(self, conn, msg):
        """
        MSG_PROPOSE is accepted only if it carries a ballotnumber greater
        than the highest ballotnumber Acceptor has received.

        Replies:
        - MSG_PROPOSE_ACCEPT carries ballotnumber and commandnumber received.
        - MSG_PROPOSE_REJECT carries the highest ballotnumber Acceptor has
        seen and the commandnumber that is received.
        """
        if msg.ballotnumber >= self.ballotnumber:
            self.logger.write("Paxos State",
                              "propose received with acceptable ballotnumber %s"
                              % str(msg.ballotnumber))
            self.ballotnumber = msg.ballotnumber
            newpvalue = PValue(msg.ballotnumber,msg.commandnumber,msg.proposal)
            self.accepted.add(newpvalue)
            replymsg = PaxosMessage(MSG_PROPOSE_ACCEPT,
                                    self.me,ballotnumber=self.ballotnumber,
                                    inresponsetoballotnumber=msg.ballotnumber,
                                    commandnumber=msg.commandnumber)
                                    #XXX self.accepted is not carried normally
        else:
            self.logger.write("Paxos State",
                              "propose received with non-acceptable ballotnumber %s"
                              % str(msg.ballotnumber))
            replymsg = PaxosMessage(MSG_PROPOSE_REJECT,
                                    self.me,ballotnumber=self.ballotnumber,
                                    inresponsetoballotnumber=msg.ballotnumber,
                                    commandnumber=msg.commandnumber)
        self.send(replymsg,peer=msg.source)

    def msg_garbagecollect(self, conn, msg):
        self.logger.write("Paxos State",
                          "Doing garbage collection upto %d" % msg.commandnumber)
        success = self.accepted.truncateto(msg.commandnumber)
        if success:
            self.objectsnapshot = (msg.commandnumber,msg.snapshot)
        else:
            self.logger.write("Garbage Collection Error",
                              "Garbege Collection failed.")
        
    def cmd_paxos(self, args):
        """
        Print the paxos state of the Acceptor.
        """
        keytuples = self.accepted.pvalues.keys()
        print sorted(keytuples, key=lambda keytuple: keytuple[0])

    def terminate_handler(self, signal, frame):
        if self.debug:
            profile_off() #turn profiling off
            print_profile_stats()
        self._graceexit()

    def _graceexit(self, exitcode=0):
        sys.stdout.flush()
        sys.stderr.flush()
        try:
            self.logger.close()
        except:
            pass
        os._exit(exitcode)

def main():
    acceptornode = Acceptor().startservice()
    signal.signal(signal.SIGINT, acceptornode.terminate_handler)
    signal.signal(signal.SIGTERM, acceptornode.terminate_handler)
    signal.pause()

if __name__=='__main__':
    main()
