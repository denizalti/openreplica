import struct
from Utils import *
from Peer import *

class Message():
    def __init__(self,serialmessage=None,source=(0,'',0,0),newpeer=(0,'',0,0),acceptors=[],leaders=[],replicas=[],type=-1,ballotnumber=(0,0),commandnumber=0,proposal='',givenpvalues=[],balance=0.0,accountid=0):
        if serialmessage == None:
            self.type = type
            self.ballotnumber = ballotnumber
            self.commandnumber = commandnumber
            self.proposal = proposal
            self.source = source
            self.newpeer = newpeer
            self.pvalues = givenpvalues
            self.acceptors = acceptors
            self.leaders = leaders
            self.replicas = replicas
            self.balance = balance
            self.accountid = accountid
        else:
            temp = serialmessage
            length, self.type = struct.unpack("II", temp[0:8])
            temp = temp[8:]
            if self.type >= MSG_HELO:
                self.source = struct.unpack("I%dsII"% ADDRLENGTH, temp[0:PEERLENGTH])
                (id,addr,port,type) = (self.source[0],self.source[1],self.source[2],self.source[3])
                addr = addr.strip("\x00")
                self.source = (id,addr,port,type)
                temp = temp[PEERLENGTH:]
                self.newpeer = struct.unpack("I%dsII"% ADDRLENGTH, temp[0:PEERLENGTH])
                (id,addr,port,type) = (self.newpeer[0],self.newpeer[1],self.newpeer[2],self.newpeer[3])
                addr = addr.strip("\x00")
                self.newpeer = (id,addr,port,type)
                temp = temp[PEERLENGTH:]
                self.balance = struct.unpack("f", temp[0:4])[0]
                temp = temp[4:]
                self.accountid = struct.unpack("f", temp[0:4])[0]
                temp = temp[4:]
                numacceptors = struct.unpack("I", temp[0:4])[0]
                temp = temp[4:]
                self.acceptors = []
                for i in range(0,numacceptors):
                    (id,addr,port,type) = struct.unpack("I%dsII"% ADDRLENGTH, temp[0:PEERLENGTH])
                    addr = addr.strip("\x00")
                    self.acceptors.append(Peer(id,addr,port,type))
                    temp = temp[PEERLENGTH:]
                numleaders = struct.unpack("I", temp[0:4])[0]
                temp = temp[4:]
                self.leaders = []
                for i in range(0,numleaders):
                    (id,addr,port,type) = struct.unpack("I%dsII"% ADDRLENGTH, temp[0:PEERLENGTH])
                    addr = addr.strip("\x00")
                    self.leaders.append(Peer(id,addr,port,type))
                    temp = temp[PEERLENGTH:]
                numreplicas = struct.unpack("I", temp[0:4])[0]
                temp = temp[4:]
                self.replicas = []
                for i in range(0,numreplicas):
                    (id,addr,port,type) = struct.unpack("I%dsII"% ADDRLENGTH, temp[0:PEERLENGTH])
                    addr = addr.strip("\x00")
                    self.replicas.append(Peer(id,addr,port,type))
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
                self.source = struct.unpack("I%dsII"% ADDRLENGTH, temp[0:PEERLENGTH])
                temp = temp[PEERLENGTH:]
                numpvalues = struct.unpack("I", temp[0:4])[0]
                temp = temp[4:]
                self.pvalues = []
                for i in range(0,numpvalues):
                    self.pvalues.append(PValue(temp[0:32]))
                    temp = temp[32:]
        
    def serialize(self):
        if self.type >= MSG_HELO:
            temp = ""
            temp += struct.pack("I", self.type)
            temp += struct.pack("I%dsII" % ADDRLENGTH, self.source[0], self.source[1], self.source[2],self.source[3])
            temp += struct.pack("I%dsII" % ADDRLENGTH, self.newpeer[0], self.newpeer[1], self.newpeer[2],self.newpeer[3])
            temp += struct.pack("f", self.balance)
            temp += struct.pack("f", self.accountid)
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
            temp += struct.pack("I%dsII" % ADDRLENGTH, self.source[0], self.source[1], self.source[2],self.source[3])
            temp += struct.pack("I", len(self.pvalues))
            for pvalue in self.pvalues:
                    temp += pvalue.serialize()
            msg = struct.pack("I", len(temp) + 4) + temp
            return msg
    
    def __str__(self):
        if self.type == MSG_NEW:
            temp = 'Message\n=======\nType: %s\nSource: (%d,%s,%d,%d)\nNewPeer: (%d,%s,%d,%d)' \
            % (messageTypes[self.type],self.source[0],self.source[1],self.source[2],self.source[3], \
               self.newpeer[0],self.newpeer[1],self.newpeer[2],self.newpeer[3])
        elif self.type >= MSG_HELO:
            temp = 'Message\n=======\nType: %s\nSource: (%d,%s,%d,%d)\nAcceptors:\n' \
            % (messageTypes[self.type],self.source[0],self.source[1],self.source[2],self.source[3])
            for acceptor in self.acceptors:
                temp += str(acceptor) + '\n'
            temp += 'Leaders:\n'
            for leader in self.leaders:
                temp += str(leader) + '\n'
            temp += 'Replicas:\n'
            for replica in self.replicas:
                temp += str(replica) + '\n'
        elif self.type >= MSG_DEBIT:
            temp = 'Message\n=======\nType: %s\nSource: (%d,%s,%d,%d)\nAccountID:\nBalance:\n' \
            % (messageTypes[self.type],self.source[0],self.source[1],self.source[2],self.source[3],\
               self.accountid,self.balance)
        else:
            temp = 'Message\n=======\nType: %s\nBallotnumber: (%d,%d)\nCommandnumber: %d\nProposal: %s\nSource: (%d,%s,%d,%d)\nPValues:\n' \
            % (messageTypes[self.type],self.ballotnumber[0],self.ballotnumber[1],self.commandnumber,self.proposal,self.source[0],self.source[1],self.source[2],self.source[3])
            for pvalue in self.pvalues:
                temp += str(pvalue) + '\n'
        return temp
        
class PValue():
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


