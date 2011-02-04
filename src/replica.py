'''
@author: denizalti
@note: The Leader
'''
from threading import Thread, Lock, Condition

from node import Node
from enums import *
from utils import *
from communicationutils import *
from connection import *
from group import *
from peer import *
from message import *
from acceptor import *
from scout import *
from commander import *
from bank import *

class Replica(Node):
    def __init__(self, replicatedobject):
        Node.__init__(self)
        self.object = replicatedobject
        
    def handleConnection(self,clientsock):
#        print "DEBUG: Handling the connection.."
        addr,port = clientsock.getpeername()
        connection = Connection(addr,port,reusesock=clientsock)
        message = Message(connection.receive())
        if message.type == MSG_HELO:
            messagesource = Peer(message.source[0],message.source[1],message.source[2],message.source[3])
            if messagesource.type == NODE_CLIENT:
                replymessage = Message(type=MSG_HELOREPLY,source=self.toPeer.serialize())
            else:
                serialgroups = {}
                for type,group in self.groups.iteritems():
                    serialgroups[type] = group.toList()
                replymessage = Message(type=MSG_HELOREPLY,source=self.toPeer.serialize(),groups=serialgroups)
            newmessage = Message(type=MSG_NEW,source=self.toPeer.serialize(),newpeer=messagesource.serialize())
            connection.send(replymessage)
            # Broadcasting MSG_NEW without waiting for a reply.
            # To add replies, first we have to add MSG_ACK & MSG_NACK
            for type,group in self.groups.iteritems():
                group.broadcastNoReply(newmessage)
            self.groups[messagesource.type].add(messagesource)
        elif message.type == MSG_HELOREPLY:
            for type,group in self.groups.iteritems():
                group.mergeList(message.groups[type])
        elif message.type == MSG_NEW:
            newpeer = Peer(message.newpeer[0],message.newpeer[1],message.newpeer[2],message.newpeer[3])
            self.groups[newpeer.type].add(newpeer)
        elif message.type == MSG_CLIENTREQUEST:
            randomleader = randint(0,len(self.leaders)-1)
            self.groups[NODE_LEADER].members[randomleader].send(message)
        elif message.type == MSG_BYE:
            messagesource = Peer(message.source[0],message.source[1],message.source[2],message.source[3])
            self.groups[messagesource.type].remove(messagesource)
        elif message.type == MSG_PERFORM:
            self.state[message.commandnumber] = message.proposal
            self.bank.executeCommand(message.proposal)
        connection.close()
   
    def cmd_object(self, args):
        print self.object

def main():
    theReplica = Replica(Bank())
    theReplica.startservice()

if __name__=='__main__':
    main()

  


    
