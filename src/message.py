import struct
from collections import Set

from enums import *
from utils import *
from peer import *

class Message():
    def __init__(self,msgtype,myname):
        self.type = msgtype
        self.source = myname

    def __str__(self):
        return 'Message: %s src %s' % (msg_names[self.type],self.source)

class PValueSet(Set):
    pass

class PValue():
    def __init__(self,serialpvalue=None,ballotnumber=(0,0),commandnumber=0,proposal=""):
        self.ballotnumber = ballotnumber
        self.commandnumber = commandnumber
        self.proposal = proposal

    def __eq__(self, otherpvalue):
        return self.ballotnumber == otherpvalue.ballotnumber and \
            self.commandnumber == otherpvalue.commandnumber and \
            self.proposal == otherpvalue.proposal

    def __ne__(self, otherpvalue):
        return not self == otherpvalue

    def __lt__(self, otherpvalue):
        return self.ballotnumber < otherpvalue.ballotnumber

    def __gt__(self, otherpvalue):
        return self.ballotnumber > otherpvalue.ballotnumber
        
    def __le__(self, otherpvalue):
        return NotImplemented

    def __ge__(self, otherpvalue):
        return NotImplemented
    
    def __str__(self):
        return 'PValue((%d,%d),%d,%s)' % (self.ballotnumber[0],self.ballotnumber[1],self.commandnumber,self.proposal.strip("\x00"))


# HELO and HELOREPLY messages
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

class PaxosMessage(Message):
    def __init__(self,msgtype, myname, ballotnumber,commandnumber=0,proposal=None,givenpvalues=None):
        Message.__init__(self, msgtype, myname)
        self.ballotnumber = ballotnumber
        self.commandnumber = commandnumber
        self.proposal = proposal
        self.pvalues = givenpvalues

    def __str__(self):
        temp = Message.__str__(self)
        temp += 'ballotnumber: %s commandnumber: %d proposal: %s pvalues: ' \
            % (msg_names[self.type],self.source, self.ballotnumber,self.commandnumber,self.proposal)
        if self.pvalues is not None:
            for pvalue in self.pvalues:
                temp += str(pvalue) + '\n'
        return temp

