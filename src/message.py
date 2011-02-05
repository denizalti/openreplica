import struct
from enums import *
from utils import *
from peer import *

class Message():
    def __init__(self,msgtype,myname):
        self.type = msgtype
        self.source = myname

    def __str__(self):
        return 'Message: %s src %s' % (msg_names[self.type],self.source)

class PValueSet():
    def __init__(self):
        self.pvalues = set()

    def remove(self,pvalue):
        if pvalue in self.pvalues:
            self.pvalues.remove(pvalue)

    def add(self,pvalue):
        if pvalue not in self.pvalues:
            self.pvalues.add(pvalue)

    def union(self,otherpvalueset):
        return self.pvalues | otherpvalueset.pvalues

    def pvaluewithmaxballotnumber(self):
        maxballotnumberpvalue = pvalue()
        for pvalue in self.pvalues:
            if pvalue.ballotnumber > maxballotnumberpvalue.ballotnumber:
                maxballotnumberpvalue = pvalue
        return maxballotnumberpvalue

    def __len__(self):
        return len(self.pvalues)

    def __str__(self):
        temp = ''
        for pvalue in self.pvalues:
            temp += pvalue
        return temp

class PValue():
    def __init__(self,ballotnumber=(0,0),commandnumber=0,proposal="",serialpvalue=None):
        self.ballotnumber = ballotnumber
        self.commandnumber = commandnumber
        self.proposal = proposal

    def id(self):
        return "%s:%d:%s" % (str(self.ballotnumber),self.commandnumber,self.proposal)

    def __hash__(self):
        return self.id().__hash__()

    def __eq__(self, otherpvalue):
        return self.ballotnumber == otherpvalue.ballotnumber and \
            self.commandnumber == otherpvalue.commandnumber and \
            self.proposal == otherpvalue.proposal
    
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
    def __init__(self,msgtype, myname, ballotnumber=0,commandnumber=0,proposal=None,givenpvalueset=None):
        Message.__init__(self, msgtype, myname)
        self.ballotnumber = ballotnumber
        self.commandnumber = commandnumber
        self.proposal = proposal
        self.pvalueset = givenpvalueset

    def __str__(self):
        temp = Message.__str__(self)
        temp += 'ballotnumber: %s commandnumber: %d proposal: %s pvalues: ' \
            % (str(self.ballotnumber),self.commandnumber,self.proposal)
        if self.pvalueset is not None:
            for pvalue in self.pvalueset:
                temp += str(pvalue) + '\n'
        return temp

