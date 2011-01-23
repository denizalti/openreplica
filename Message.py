import struct
from Utils import *
from Peer import *

# The Ordering is as follows:
#length
#type
#ballotnumber
#commandnumber
#proposallength  
#proposal
#source
#numpvalues
#pvalues

class Message():
    def __init__(self,serialmessage=None,source=(0,'',0),acceptors=[],leaders=[],replicas=[],type=-1,ballotnumber=(0,0),commandnumber=0,proposal='',givenpvalues=[]):
        if serialmessage == None:
            self.type = type
            self.ballotnumber = ballotnumber
            self.commandnumber = commandnumber
            self.proposal = proposal
            self.source = source
            self.pvalues = givenpvalues
            self.acceptors = acceptors
            self.leaders = leaders
            self.replicas = replicas
        else:
            temp = serialmessage
            length, self.type = struct.unpack("II", temp[0:8])
            temp = temp[8:]
            if self.type == MSG_HELO or MSG_HELOREPLY or MSG_NEW:
                self.source = struct.unpack("I%dsI"% ADDRLENGTH, temp[0:PEERLENGTH])
                (id,addr,port) = (self.source[0],self.source[1],self.source[2])
                addr = addr.strip("\x00")
                self.source = (id,addr,port)
                temp = temp[PEERLENGTH:]
                numacceptors = struct.unpack("I", temp[0:4])[0]
                temp = temp[4:]
                self.acceptors = []
                for i in range(0,numacceptors):
                    (id,addr,port) = struct.unpack("I%dsI"% ADDRLENGTH, temp[0:PEERLENGTH])
                    addr = addr.strip("\x00")
                    self.acceptors.append(Peer(id,addr,port))
                    temp = temp[PEERLENGTH:]
                numleaders = struct.unpack("I", temp[0:4])[0]
                temp = temp[4:]
                self.leaders = []
                for i in range(0,numleaders):
                    (id,addr,port) = struct.unpack("I%dsI"% ADDRLENGTH, temp[0:PEERLENGTH])
                    addr = addr.strip("\x00")
                    self.leaders.append(Peer(id,addr,port))
                    temp = temp[PEERLENGTH:]
                numreplicas = struct.unpack("I", temp[0:4])[0]
                temp = temp[4:]
                self.replicas = []
                for i in range(0,numreplicas):
                    (id,addr,port) = struct.unpack("I%dsI"% ADDRLENGTH, temp[0:PEERLENGTH])
                    addr = addr.strip("\x00")
                    self.replicas.append(Peer(id,addr,port))
                    temp = temp[PEERLENGTH:]
            else:    
                self.ballotnumber = struct.unpack("II", temp[0:8])
                temp = temp[8:]
                self.commandnumber = struct.unpack("I", temp[0:4])[0]
                temp = temp[4:]
                proposallength = struct.unpack("I", temp[0:4])[0]
                temp = temp[4:]
                self.proposal = struct.unpack("%ds" % proposallength,temp[0:proposallength])[0]
                temp = temp[proposallength:]
                self.source = struct.unpack("I%dsI"% ADDRLENGTH, temp[0:PEERLENGTH])
                temp = temp[PEERLENGTH:]
                numpvalues = struct.unpack("I", temp[0:4])[0]
                temp = temp[4:]
                self.pvalues = []
                for i in range(0,numpvalues):
                    self.pvalues.append(pvalue(temp[0:32]))
                    temp = temp[32:]
        
    def serialize(self):
        if self.type == MSG_HELO or MSG_HELOREPLY or MSG_NEW:
            temp = ""
            temp += struct.pack("I", self.type)
            temp += struct.pack("I15sI", self.source[0], self.source[1], self.source[2])
            temp += struct.pack("I", len(self.acceptors))
            for acceptor in self.acceptors:
                temp += acceptor.pack()
            temp += struct.pack("I", len(self.leaders))
            for leader in self.leaders:
                temp += leader.pack()
            temp += struct.pack("I", len(self.replicas))
            for replica in self.replicas:
                temp += replica.pack()
            msg = struct.pack("I", len(temp) + 4) + temp
            return msg
        else:
            temp = ""
            temp += struct.pack("I", self.type)
            temp += struct.pack("I", self.ballotnumber[0])
            temp += struct.pack("I", self.ballotnumber[1])
            temp += struct.pack("I", self.commandnumber)
            temp += struct.pack("I", len(self.proposal))
            temp += struct.pack("%ds" % len(self.proposal), self.proposal)
            temp += struct.pack("I%dsI" % ADDRLENGTH, self.source[0], self.source[1], self.source[2])
            temp += struct.pack("I", len(self.pvalues))
            for pvalue in self.pvalues:
                    temp += pvalue.serialize()
            msg = struct.pack("I", len(temp) + 4) + temp
            print "Test!!!"
            print self.testTheMessage(msg)
            return msg
    
    def testTheMessage(self, temporary):
        testing = Message(temporary)
        return str(testing)
    
    def __str__(self):
        if self.type == MSG_HELO or MSG_HELOREPLY or MSG_NEW:
            temp = 'Message\n=======\nType: %d\nSource: (%d,%s,%d)\nAcceptors:\n' \
            % (self.type,self.source[0],self.source[1],self.source[2])
            for acceptor in self.acceptors:
                temp += str(acceptor) + '\n'
            temp += 'Leaders:\n'
            for leader in self.leaders:
                temp += str(leader) + '\n'
            temp += 'Replicas:\n'
            for replica in self.replicas:
                temp += str(replica) + '\n'
            return temp
        else:
            temp = 'Message\n=======\nType: %d\nBallotnumber: (%d,%d)\nCommandnumber: %d\nProposal: %s\nSource: (%d,%s,%d)\nPValues:\n' \
            % (self.type,self.ballotnumber[0],self.ballotnumber[1],self.commandnumber,self.proposal,self.source[0],self.source[1],self.source[2])
            for pvalue in self.pvalues:
                temp += str(pvalue) + '\n'
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


