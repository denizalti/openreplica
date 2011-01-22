import struct
from Utils import *

# The Ordering is as follows:
#length
#type
#ballotnumber
#commandnumber
#proposallength  
#proposal
#numpvalues
#pvalues

class Message():
    def __init__(self,serialmessage=None,source=(0,'',0),type=-1,ballotnumber=(0,0),commandnumber=0,proposal='',givenpvalues=[]):
        if serialmessage == None:
            self.type = type
            self.ballotnumber = ballotnumber
            self.commandnumber = commandnumber
            self.proposal = proposal
            self.numpvalues = len(givenpvalues)
            self.pvalues = givenpvalues
        else:
            temp = serialmessage
            length, self.type = struct.unpack("II", temp[0:8])
            temp = temp[8:]
            self.ballotnumber = struct.unpack("II", temp[0:8])
            temp = temp[8:]
            self.commandnumber = struct.unpack("I", temp[0:4])[0]
            temp = temp[4:]
            proposallength = struct.unpack("I", temp[0:4])[0]
            temp = temp[4:]
            self.proposal = struct.unpack("%ds" % proposallength,temp[0:proposallength])[0]
            temp = temp[proposallength:]
            self.numpvalues = struct.unpack("I", temp[0:4])[0]
            temp = temp[4:]
            self.pvalues = []
            for i in range(0,self.numpvalues):
                self.pvalues.append(pvalue(temp[0:32]))
                temp = temp[32:]
        
    def serialize(self):
        temp = ""
        temp += struct.pack("I", self.type)
        print self.ballotnumber[0]
        temp += struct.pack("I", self.ballotnumber[0])
        temp += struct.pack("I", self.ballotnumber[1])
        temp += struct.pack("I", self.commandnumber)
        temp += struct.pack("I", len(self.proposal))
        temp += struct.pack("%ds" % len(self.proposal), self.proposal)
        temp += struct.pack("I", self.numpvalues)
        for i in range(0,self.numpvalues):
                temp += self.pvalues[i].serialize()
        msg = struct.pack("I", len(temp) + 4) + temp
        print "Test!!!"
        print self.testTheMessage(msg)
        return msg
    
    def testTheMessage(self, temporary):
        testing = Message(temporary)
        return str(testing)
    
    def __str__(self):
        temp = 'Message\n=======\nType: %d\nBallotnumber: (%d,%d)\nCommandnumber: %d\nProposal: %s\nPValues:\n' \
        % (self.type,self.ballotnumber[0],self.ballotnumber[1],self.commandnumber,self.proposal)
        for i in range(0,self.numpvalues):
            temp += str(self.pvalues[i]) + '\n'
        return temp
    
class pvalue():
    def __init__(self,serialpvalue=None,ballotnumber=(0,0),commandnumber=0,proposal=""):
        if serialpvalue == None:
            self.ballotnumber = ballotnumber
            self.commandnumber = commandnumber
            self.proposal = proposal
        else:
            temp = serialpvalue
            self.ballotnumber = struct.unpack("II", temp[0:8])
            temp = temp[8:]
            self.commandnumber = struct.unpack("I", temp[0:4])[0]
            temp = temp[4:]
            self.proposal = struct.unpack("20s",temp)[0]
            
    def serialize(self):
        temp = ""
        temp += struct.pack("II", self.ballotnumber[0],self.ballotnumber[1])
        temp += struct.pack("I", self.commandnumber)
        temp += struct.pack("20s", self.proposal)
        return temp
        
    def __eq__(self, otherpvalue):
        if (self.ballotnumber == otherpvalue.ballotnumber and \
            self.commandnumber == otherpvalue.commandnumber and \
            self.proposal == otherpvalue.proposal):
            return True
        else:
            return False
        
    def __lt__(self, otherpvalue):
        if (self.ballotnumber[1]<=otherpvalue.ballotnumber[1]):
            if (self.ballotnumber[0]<otherpvalue.ballotnumber[0]):
                return True
        return False
    
    def __gt__(self, otherpvalue):
        if (self.ballotnumber[0]>=otherpvalue.ballotnumber[0]):
            if (self.ballotnumber[1]>otherpvalue.ballotnumber[1]):
                return True
        return False
        
    def __str__(self):
        return 'pvalue((%d,%d),%d,%s)' % (self.ballotnumber[0],self.ballotnumber[1],self.commandnumber,self.proposal.strip("\x00"))


