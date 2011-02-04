import struct
from enums import *
from utils import *
from peer import *

class Message():
    def __init__(self,source=(0,'',0,0),newpeer=(0,'',0,0),groups={NODE_ACCEPTOR:[],NODE_REPLICA:[],NODE_LEADER:[]},\
                 type=-1,ballotnumber=(0,0),commandnumber=0,proposal='',givenpvalues=[],balance=0.0,accountid=0):
        self.type = type
        self.ballotnumber = ballotnumber
        self.commandnumber = commandnumber
        self.proposal = proposal
        self.source = source
        self.newpeer = newpeer
        self.pvalues = givenpvalues
        self.groups = groups
        self.balance = balance
        self.accountid = accountid

    def __str__(self):
        if self.type == MSG_NEW:
            return 'Message: %s src %s new %s' % (msg_names[self.type],self.source,self.newpeer)
        elif self.type == MSG_HELO or self.type == MSG_HELOREPLY:
            temp = 'Message: %s src %s groups ' % (msg_names[self.type],self.source)
            for type,group in self.groups:
                for node in group:
                    temp += str(node) + '\n'
            return temp
        else:
            temp = 'Message: %s src %s ballotnumber: (%d,%d) commandnumber: %d proposal: %s \nSource: (%d,%s,%d,%d)\nPValues:\n' \
            % (msg_names[self.type],self.source, self.ballotnumber[0],self.ballotnumber[1],self.commandnumber,self.proposal)
            for pvalue in self.pvalues:
                temp += str(pvalue) + '\n'
        return temp

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


