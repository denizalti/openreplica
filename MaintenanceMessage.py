import struct
from Utils import *

# The Ordering is as follows:
#length
#type
#source
#numacceptors
#acceptors
#numleaders
#leaders
#numreplicas
#replicas

class MaintenanceMessage():
    def __init__(self,serialmessage=None,type=-1,source=(0,'',0),acceptors=[],leaders=[],replicas=[]):
        if serialmessage == None:
            self.type = type
            self.source = source
            self.acceptors = acceptors
            self.leaders = leaders
            self.replicas = replicas
        else:
            temp = serialmessage
            length, self.type = struct.unpack("II", temp[0:8])
            temp = temp[8:]
            self.source = struct.unpack("I%dsI"% ADDRLENGTH, temp[0:PEERLENGTH])
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
        
    def serialize(self):
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
        return temp
    
    def testTheMessage(self, temporary):
        testing = MaintenanceMessage(temporary)
        return str(testing)
    
    def __str__(self):
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
