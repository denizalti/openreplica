"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: The Acceptor keeps track of past Paxos ballots. It is the log for the Paxos state.
@copyright: See LICENSE
"""
import signal
import cPickle as pickle
from pack import *
from concoord.node import *
from concoord.enums import *
from concoord.utils import *
from concoord.pack import *
from concoord.pvalue import PValueSet
from concoord.message import *

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
        if self.durable:
            self.file = open('concoordlog', 'a')
        self.ballotnumber = (0,0)
        self.last_accept_msg_id = -1
        self.accepted = PValueSet()
        self.objectsnapshot = (0,None)

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
            if self.debug: self.logger.write("Paxos State",
                              "prepare received with acceptable ballotnumber %s"
                              % str(msg.ballotnumber))

            self.ballotnumber = msg.ballotnumber
            self.last_accept_msg_id = msg.id
            replymsg = create_message(MSG_PREPARE_ADOPTED, self.me,
                                      {FLD_BALLOTNUMBER: self.ballotnumber,
                                       FLD_INRESPONSETO: msg.ballotnumber,
                                       FLD_PVALUESET: self.accepted.pvalues})
        # or else it should be a precise duplicate of the last request
        # in this case we do nothing
        elif msg.ballotnumber == self.ballotnumber and \
                msg.id == self.last_accept_msg_id:
            if self.debug: self.logger.write("Paxos State","message received before: %s" % msg)
            return
        else:
            if self.debug: self.logger.write("Paxos State",
                              ("prepare received with non-acceptable "
                               "ballotnumber %s ") % (str(msg.ballotnumber),))
            self.last_accept_msg_id = msg.id
            replymsg = create_message(MSG_PREPARE_PREEMPTED, self.me,
                                      {FLD_BALLOTNUMBER: self.ballotnumber,
                                       FLD_INRESPONSETO: msg.ballotnumber,
                                       FLD_PVALUESET: self.accepted.pvalues})

        if self.debug: self.logger.write("Paxos State", "prepare responding with %s"
                          % str(replymsg))
        conn.send(replymsg)

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
            if self.debug: self.logger.write("Paxos State",
                              "propose received with acceptable ballotnumber %s"
                              % str(msg.ballotnumber))
            self.ballotnumber = msg.ballotnumber
            newpvalue = PValue(msg.ballotnumber,msg.commandnumber,msg.proposal)
            self.accepted.add(newpvalue)
            replymsg = create_message(MSG_PROPOSE_ACCEPT, self.me,
                                      {FLD_BALLOTNUMBER: self.ballotnumber,
                                       FLD_INRESPONSETO: msg.ballotnumber,
                                       FLD_COMMANDNUMBER: msg.commandnumber})
            conn.send(replymsg)
            if self.durable:
                self.file.write(str(newpvalue))
                os.fsync(self.file)
        else:
            if self.debug: self.logger.write("Paxos State",
                              "propose received with non-acceptable ballotnumber %s"
                              % str(msg.ballotnumber))
            replymsg = create_message(MSG_PROPOSE_REJECT, self.me,
                                      {FLD_BALLOTNUMBER: self.ballotnumber,
                                       FLD_INRESPONSETO: msg.ballotnumber,
                                       FLD_COMMANDNUMBER: msg.commandnumber})
            conn.send(replymsg)

    def msg_garbagecollect(self, conn, msg):
        if self.debug: self.logger.write("Paxos State",
                          "Doing garbage collection upto %d" % msg.commandnumber)
        success = self.accepted.truncateto(msg.commandnumber)
        if success:
            self.objectsnapshot = (msg.commandnumber,pickle.loads(msg.snapshot))
        else:
            if self.debug: self.logger.write("Garbage Collection Error",
                              "Garbege Collection failed.")

    def cmd_paxos(self, args):
        """
        Print the paxos state of the Acceptor.
        """
        keytuples = self.accepted.pvalues.keys()
        print sorted(keytuples, key=lambda keytuple: keytuple[0])

    def terminate_handler(self, signal, frame):
        self._graceexit()

    def _graceexit(self, exitcode=0):
        sys.stdout.flush()
        sys.stderr.flush()
        if hasattr(self, 'logger'): self.logger.close()
        os._exit(exitcode)

def main():
    acceptornode = Acceptor().startservice()
    signal.signal(signal.SIGINT, acceptornode.terminate_handler)
    signal.signal(signal.SIGTERM, acceptornode.terminate_handler)
    signal.pause()

if __name__=='__main__':
    main()
