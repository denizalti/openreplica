import struct

# The Ordering is as follows:
length          #4
type            #4
ballotnumber    #8
commandnumber   #4
proposal        #20
source          #12
numpvalues      #4
pvalues         #*32

class Message():
    def __init__(self,serialmessage=None,type=-1,source=(0,'',0),ballotnumber=(0,0),commandnumber=0,proposal='',givenpvalues=[]):
        if serialmessage == None:
            self.type = type
            self.ballotnumber = ballotnumber
            self.commandnumber = commandnumber
            self.proposal = proposal
            self.source = source
            self.numpvalues = len(givenpvalues)
            self.pvalues = givenpvalues
            self.length = 56+self.numpvalues*PVALUELENGTH
        else:
            temp = serialmessage
            self.length = struct.unpack("I", temp[0:4])[0]
            temp = temp[4:]
            self.type = struct.unpack("I", temp[0:4])[0]
            temp = temp[4:]
            self.ballotnumber = struct.unpack("II", temp[0:8])
            temp = temp[8:]
            self.commandnumber = struct.unpack("I", temp[0:4])[0]
            temp = temp[4:]
            self.proposal = struct.unpack("20s",temp)[0]
            temp = temp[20:]
            self.source = struct.unpack("III", temp[0:12])
            temp = temp[12:]
            self.numpvalues = struct.unpack("I", temp[0:4])[0]
            temp = temp[4:]
            self.pvalues = []
            for i in range(0,self.numpvalues):
                self.pvalues.append(pvalue(temp[0:32]))
                temp = temp[32:]
        
    def serialize(self):
        temp = ""
        temp += struct.pack("I", self.length)
        temp += struct.pack("I", self.type)
        temp += struct.pack("I", self.ballotnumber[0])
        temp += struct.pack("I", self.ballotnumber[1])
        temp += struct.pack("I", self.commandnumber)
        temp += struct.pack("20s", self.proposal)
        temp += struct.pack("I", self.source[0])
        temp += struct.pack("I", self.source[1])
        temp += struct.pack("I", self.source[2])
        temp += struct.pack("I", self.numpvalues)
        for i in range(0,self.numpvalues):
                temp += self.pvalues[i].serialize()
        return temp
    
    def __str__(self):
        temp = 'Message\n=======\nType: %d\n Ballotnumber: (%d,%d)\nCommandnumber: %d\nProposal: %s\n,Length: %d\nPValues:\n' \
        % (self.type,self.ballotnumber[0],self.ballotnumber[1],self.commandnumber,self.proposal,self.length)
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


