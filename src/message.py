"""
@author: denizalti
@note: Message
@date: February 1, 2011
"""
from threading import Lock

from enums import *
from utils import *
from peer import Peer
from command import Command


msgidpool = 0
msgidpool_lock=Lock()

class Message():
    """Message encloses the basic state that is shared
    by all types of messages in the system.
    """
    def __init__(self,msgtype,myname):
        """Initialize Message

        Message State
        - type: type of message (see enums.py)
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
            if self.type != MSG_ACK:
                self.id = msgidpool
                msgidpool += 1
        return self

    def fullid(self):
        return "%s+%d" % (self.source.id(), self.id)

    def __str__(self):
        """Return Message information"""
        if self.type != MSG_ACK:
            return 'Message#%d: %s src %s' % (self.id,msg_names[self.type],self.source)
        else:
            return 'AckMessage#%d: %s src %s' % (self.ackid,msg_names[self.type],self.source)

class HandshakeMessage(Message):
    def __init__(self,msgtype,myname,groups=None):
        Message.__init__(self, msgtype, myname)
        if groups != None:
            self.groups = groups

    def __str__(self):
        temp = Message.__str__(self)
        if self.type == MSG_HELOREPLY:
            temp = '%s groups %s' % (temp, self.groups)
        return temp

class UpdateMessage(Message):
    def __init__(self,msgtype,myname,decisions=None):
        Message.__init__(self, msgtype, myname)
        if decisions != None:
            self.decisions = decisions

    def __str__(self):
        temp = Message.__str__(self)
        if self.type == MSG_UPDATEREPLY:
            temp = '%s decisions %s' % (temp, self.decisions)
        return temp

class PaxosMessage(Message):
    def __init__(self,msgtype, myname, ballotnumber=0,inresponsetoballotnumber=0,commandnumber=0,proposal=None,givenpvalueset=None,result=None):
        Message.__init__(self, msgtype, myname)
        self.ballotnumber = ballotnumber
        self.inresponseto = inresponsetoballotnumber
        self.commandnumber = commandnumber
        self.proposal = proposal
        self.pvalueset = givenpvalueset
        self.result = result

    def __str__(self):
        temp = '%sballotnumber: %s commandnumber: %d proposal: %s result: %s pvalues: ' \
            % (Message.__str__(self),str(self.ballotnumber),self.commandnumber,self.proposal,self.result)
        if self.pvalueset is not None:
            ps = "\n".join(str(pvalue) for pvalue in self.pvalueset.pvalues)
            temp = "%s\n%s" % (temp, ps)
        return temp

class ClientMessage(Message):
    def __init__(self, msgtype, myname, command=None, inresponseto=0):
        Message.__init__(self, msgtype, myname)
        self.command = command
        self.inresponseto = inresponseto

    def __str__(self):
        return "%s inresponseto: %d  request: %s" % (Message.__str__(self), self.inresponseto, str(self.command))

class ClientReplyMessage(Message):
    def __init__(self, msgtype, myname, reply=None, replycode=-1, inresponseto=0):
        Message.__init__(self, msgtype, myname)
        self.reply = reply
        self.replycode = replycode
        self.inresponseto = inresponseto

    def __str__(self):
        return "%s inresponseto: %d  reply: %s replycode: %s" % (Message.__str__(self), self.inresponseto, str(self.reply), cr_codes[self.replycode])

class AckMessage(Message):
    def __init__(self,msgtype, myname, ackid):
        Message.__init__(self, msgtype, myname)
        self.ackid = ackid

class ReferMessage(Message):
    def __init__(self, msgtype, myname, referredpeer=None):
        Message.__init__(self, msgtype, myname)
        self.referredpeer = referredpeer

    def __str__(self):
        return "%s referredpeer: %s" % (Message.__str__(self), str(self.referredpeer))

class QueryMessage(Message):
    def __init__(self,msgtype, myname, peers=None):
        Message.__init__(self, msgtype, myname)
        if peers != None:
            self.peers = peers

    def __str__(self):
        temp = Message.__str__(self)
        if self.peers != None:
            temp += ' peers %s' % self.peers
        return temp

class MessageInfo():
    """MessageState encloses a message, destination, messagestate and timestamp"""
    def __init__(self, message, destination, messagestate=ACK_NOTACKED, timestamp=0):
        """Initialize MessageInfo

        MessageInfo State
        - message: Message object
        - destination: destination of the message
        - messagestate: indicates if the message has been ACKed or not [NOTACKEDYET | ACKED]
        - timestamp: timestamp for the last action
        """
        self.message = message
        self.destination = destination
        self.messagestate = messagestate
        self.timestamp = timestamp

    def __str__(self):
        return "%d: [%s] %s %.2f" % (self.message.id, self.destination, msg_states[self.messagestate], self.timestamp)
