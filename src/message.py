"""
@author: denizalti
@note: Message, PValueSet, PValue
@date: February 1, 2011
"""
import struct
from enums import *
from utils import *
from peer import *
from threading import Lock

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
            temp += ' groups %s' % self.groups
        return temp

class UpdateMessage(Message):
    def __init__(self,msgtype,myname,decisions=None):
        Message.__init__(self, msgtype, myname)
        if decisions != None:
            self.decisions = decisions

    def __str__(self):
        temp = Message.__str__(self)
        if self.type == MSG_UPDATEREPLY:
            temp += ' decisions %s' % self.decisions
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
        temp = Message.__str__(self)
        temp += 'ballotnumber: %s commandnumber: %d proposal: %s result: %s pvalues: ' \
            % (str(self.ballotnumber),self.commandnumber,self.proposal,self.result)
        if self.pvalueset is not None:
            for pvalue in self.pvalueset.pvalues:
                temp += str(pvalue) + '\n'
        return temp

class ClientMessage(Message):
    def __init__(self,msgtype,myname,command=None,inresponseto=0):
        Message.__init__(self, msgtype, myname)
        self.command = command
        self.inresponseto = inresponseto # command number this reply is in response to

    def __str__(self):
        temp = Message.__str__(self)
        temp += '  inresponseto: %d' % self.inresponseto
        if self.type == MSG_CLIENTREQUEST:
            temp += '  request: %s' % str(self.command)
        elif self.type == MSG_CLIENTREPLY:
            temp += '  reply: %s' % str(self.command)
        return temp

class AckMessage(Message):
    def __init__(self,msgtype, myname, ackid):
        Message.__init__(self, msgtype, myname)
        self.ackid = ackid

class QueryMessage(Message):
    def __init__(self,msgtype, myname, groups=None):
        Message.__init__(self, msgtype, myname)
        if groups != None:
            self.groups = groups

    def __str__(self):
        temp = Message.__str__(self)
        if self.groups != None:
            temp += ' groups %s' % self.groups
        return temp

class Command():
    """Command encloses a client, clientcommandnumber and command"""
    def __init__(self,client=None,clientcommandnumber=0,command=""):
        """Initialize Command

        Command State
        - client
        - clientcommandnumber: unique id for the command, specific to Client
                               doesn't affect paxos commandnumber
        - command: command to be executed
        """
        self.client = client
        self.clientcommandnumber = clientcommandnumber
        self.command = command

    def __hash__(self):
        """Returns the hashed command"""
        return hash(str(self.client)+str(self.clientcommandnumber)+str(self.command))

    def __eq__(self, othercommand):
        """Equality function for two Commands.
        Returns True if given Command is equal to Command, False otherwise.
        """
        return self.client == othercommand.client and \
            self.clientcommandnumber == othercommand.clientcommandnumber and \
            self.command == othercommand.command

    def __ne__(self, othercommand):
        """Non-equality function for two Commands.
        Returns True if given Command is not equal to Command, False otherwise.
        """
        return self.client != othercommand.client or \
            self.clientcommandnumber != othercommand.clientcommandnumber or \
            self.command != othercommand.command
    
    def __str__(self):
        """Returns Command information"""
        return 'Command(%s,%d,%s)' % (str(self.client),self.clientcommandnumber,self.command)

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
