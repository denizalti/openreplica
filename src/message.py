"""
@author: denizalti
@note: Message, PValueSet, PValue
@date: February 1, 2011
"""

import struct
from enums import *
from utils import *
from peer import *

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

    def __str__(self):
        """Return Message information"""
        return 'Message: %s src %s' % (msg_names[self.type],self.source)

class PValueSet():
    """PValueSet encloses a set of pvalues and supports corresponding
    set functions.
    """
    def __init__(self):
        """Initialize PValueSet

        PValueSet State
        - pvalues: set of PValues
        """
        self.pvalues = set()

    def remove(self,pvalue):
        """Removes given pvalue from the PValueSet"""
        if pvalue in self.pvalues:
            self.pvalues.remove(pvalue)

    def add(self,pvalue):
        """Adds given PValue to the PValueSet"""
        if pvalue not in self.pvalues:
            self.pvalues.add(pvalue)

    def union(self,otherpvalueset):
        """Unionizes the pvalues of given PValueSet with the pvalues of the PValueSet"""
        return self.pvalues | otherpvalueset.pvalues

    def pickMaxBallotNumber(self):
        """Returns the PValue in pvalues with the highest ballotnumber"""
        maxballotnumberpvalue = PValue()
        for pvalue in self.pvalues:
            if pvalue.ballotnumber > maxballotnumberpvalue.ballotnumber:
                maxballotnumberpvalue = pvalue
        return maxballotnumberpvalue

    def pMax(self):
        """Returns a  mapping from command numbers to proposals with the highest ballotnumbers"""
        commandnumbers = [pvalue.commandnumber for pvalue in self.pvalues]
        pmaxresult = {}
        maxballotnumberpvalue = PValue()
        for c in commandnumbers:
            for pvalue in self.pvalues:
                if pvalue.commandnumber == c and pvalue.ballotnumber > maxballotnumberpvalue.ballotnumber:
                    maxballotnumberpvalue = pvalue
            pmaxresult[c] = maxballotnumberpvalue.proposal
        return pmaxresult

    def __len__(self):
        """Returns the number of PValues in the PValueSet"""
        return len(self.pvalues)

    def __str__(self):
        """Returns PValueSet information"""
        temp = ''
        for pvalue in self.pvalues:
            temp += str(pvalue)
        return temp

class PValue():
    """PValue encloses a ballotnumber, commandnumber and proposal.
    PValue is used to keep Paxos state in Acceptor and Leader nodes.
    """
    def __init__(self,ballotnumber=(0,0),commandnumber=0,proposal="",serialpvalue=None):
        """Initialize PValue

        PValue State
        - ballotnumber: ballotnumber for the PValue
        - commandnumber: commandnumber for the PValue
        - proposal: proposal for the PValue
        """
        self.ballotnumber = ballotnumber
        self.commandnumber = commandnumber
        self.proposal = proposal

    def id(self):
        """Returns the id (ballotnumber:commandnumber:proposal) of the PValue"""
        return "%s:%d:%s" % (str(self.ballotnumber),self.commandnumber,self.proposal)

    def __hash__(self):
        """Returns the hashed id"""
        return self.id().__hash__()

    def __eq__(self, otherpvalue):
        """Equality function for two PValues.
        Returns True if given PValue is equal to PValue, False otherwise.
        """
        return self.ballotnumber == otherpvalue.ballotnumber and \
            self.commandnumber == otherpvalue.commandnumber and \
            self.proposal == otherpvalue.proposal
    
    def __str__(self):
        """Returns PValue information"""
        return 'PValue((%d,%s),%d,%s)' % (self.ballotnumber[0],self.ballotnumber[1],self.commandnumber,self.proposal.strip("\x00"))


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
    def __init__(self,msgtype,myname,command=None):
        Message.__init__(self, msgtype, myname)
        self.proposal = command

    def __str__(self):
        temp = Message.__str__(self)
        if self.type == MSG_CLIENTREQUEST:
            temp += '  request: %s' % self.proposal
        elif self.type == MSG_CLIENTREPLY:
            temp += '  reply: %s' % self.proposal
        return temp

class Command():
    """Command encloses a clientid, clientcommandnumber and command"""
    def __init__(self,clientid=(0,0),clientcommandnumber=0,command="",serialpvalue=None):
        """Initialize PValue

        PValue State
        - ballotnumber: ballotnumber for the PValue
        - commandnumber: commandnumber for the PValue
        - proposal: proposal for the PValue
        """
        self.ballotnumber = ballotnumber
        self.commandnumber = commandnumber
        self.proposal = proposal

    def id(self):
        """Returns the id (ballotnumber:commandnumber:proposal) of the PValue"""
        return "%s:%d:%s" % (str(self.ballotnumber),self.commandnumber,self.proposal)

    def __hash__(self):
        """Returns the hashed id"""
        return self.id().__hash__()

    def __eq__(self, otherpvalue):
        """Equality function for two PValues.
        Returns True if given PValue is equal to PValue, False otherwise.
        """
        return self.ballotnumber == otherpvalue.ballotnumber and \
            self.commandnumber == otherpvalue.commandnumber and \
            self.proposal == otherpvalue.proposal
    
    def __str__(self):
        """Returns PValue information"""
        return 'PValue((%d,%s),%d,%s)' % (self.ballotnumber[0],self.ballotnumber[1],self.commandnumber,self.proposal.strip("\x00"))
