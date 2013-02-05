"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Messages sent on the wire
@copyright: See LICENSE
"""
from threading import Lock
from concoord.enums import *
from concoord.utils import *
from pack import *
msgidpool = 0
msgidpool_lock=Lock()

class Message():
    """Message encloses the basic state that is shared
    by all types of messages in the system.
    """
    def __init__(self, msgtype, myname):
        """Message state
        - type: type of message as defined in enums.py
        - source: Peer instance of the source
        """
        self.type = msgtype
        self.source = myname
        self.assignuniqueid()

    def assignuniqueid(self):
        """Assign a new unique id to this message"""
        global msgidpool
        global msgidpool_lock

        with msgidpool_lock:
            self.id = msgidpool
            msgidpool += 1
        return self

    def fullid(self):
        return "%s+%d" % (getpeerid(self.source), self.id)

    def __str__(self):
        return 'Message#%d: %s src %s' % (self.id,
                                          msg_names[self.type],
                                          self.source)

class HandshakeMessage(Message):
    def __init__(self, msgtype, myname, leader=None):
        Message.__init__(self, msgtype, myname)
        if leader:
            self.leader = leader

    def __str__(self):
        temp = Message.__str__(self)
        if self.type == MSG_HELOREPLY:
            temp = '%s Leader: %s' % (temp, str(self.leader))
        return temp

class UpdateMessage(Message):
    def __init__(self, msgtype, myname, decisions=None):
        Message.__init__(self, msgtype, myname)
        self.decisions = decisions

    def __str__(self):
        temp = Message.__str__(self)
        if self.type == MSG_UPDATEREPLY:
            temp = '%s decisions %s' % (temp, self.decisions)
        return temp

class PaxosMessage(Message):
    def __init__(self,
                 msgtype,
                 myname,
                 ballotnumber=0,
                 inresponsetoballotnumber=0,
                 commandnumber=0,
                 proposal=None,
                 givenpvalueset=None,
                 result=None):
        Message.__init__(self, msgtype, myname)
        self.ballotnumber = ballotnumber
        self.inresponseto = inresponsetoballotnumber
        self.commandnumber = commandnumber
        self.proposal = proposal
        self.pvalueset = givenpvalueset
        self.result = result

    def __str__(self):
        temp = '%sballotnumber: %s commandnumber: %d proposal: %s result: %s pvalues: ' \
            % (Message.__str__(self),
               str(self.ballotnumber),
               self.commandnumber,
               self.proposal,
               self.result)
        if self.pvalueset is not None:
            ps = "\n".join(str(pvalue) for pvalue in self.pvalueset.pvalues)
            temp = "%s\n%s" % (temp, ps)
        return temp

class ClientMessage(Message):
    def __init__(self, msgtype, myname,
                 command=None, inresponseto=0, token=None):
        Message.__init__(self, msgtype, myname)
        self.command = command
        self.inresponseto = inresponseto
        self.token = token

    def __str__(self):
        return "%s inresponseto: %d  request: %s token: %s" \
            % (Message.__str__(self),
               self.inresponseto,
               str(self.command),
               self.token)

class ClientReplyMessage(Message):
    def __init__(self, msgtype, myname,
                 reply=None, replycode=-1, inresponseto=0):
        Message.__init__(self, msgtype, myname)
        self.reply = reply
        self.replycode = replycode
        self.inresponseto = inresponseto

    def __str__(self):
        return "%s inresponseto: %d  reply: %s replycode: %s" \
            % (Message.__str__(self), self.inresponseto,
               str(self.reply), cr_codes[self.replycode])

class GarbageCollectMessage(Message):
    def __init__(self, msgtype, myname, commandnumber=0, snapshot=None):
        Message.__init__(self, msgtype, myname)
        self.commandnumber = commandnumber
        self.snapshot = snapshot

    def __str__(self):
        return "%s commandnumber: %d snapshot: %s" \
            % (Message.__str__(self), self.commandnumber, str(self.snapshot))

class StatusMessage():
    def __init__(self):
        self.type = MSG_STATUS

    def __str__(self):
        return 'Status Message'

class MessageInfo():
    """This class is used to ensure that all messages are
    ultimately delivered to their destinations"""
    def __init__(self, message, destination, timestamp=0):
        self.message = message
        self.destination = destination
        self.timestamp = timestamp

    def __str__(self):
        return "%d: [%s] %.2f" % (self.message.id,
                                  self.destination,
                                  self.timestamp)
