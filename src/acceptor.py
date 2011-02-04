'''
@author: denizalti
@note: The Acceptor acts like a server.
'''
from threading import Thread
from random import randint
import threading

from node import Node
from enums import *
from utils import *
from communicationutils import *
from connection import *
from group import *
from peer import *
from message import *

class Acceptor(Node):
    def __init__(self):
        Node.__init__(self)

        # Synod Acceptor State
        self.ballotnumber = (0,0)
        self.accepted = [] # Array of pvalues
        
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
        elif message.type == MSG_DEBIT:
            randomleader = randint(0,len(self.leaders)-1)
            self.leaders[randomleader].send(message)
        elif message.type == MSG_DEPOSIT:
            randomleader = randint(0,len(self.leaders)-1)
            self.leaders[randomleader].send(message)
        elif message.type == MSG_BYE:
            messagesource = Peer(message.source[0],message.source[1],message.source[2],message.source[3])
            self.groups[messagesource.type].remove(messagesource)
        elif message.type == MSG_PREPARE:
            if message.ballotnumber > self.ballotnumber:
                print "ACCEPTOR got a PREPARE with Ballotnumber: ", message.ballotnumber
                print "ACCEPTOR's Ballotnumber: ", self.ballotnumber
                self.ballotnumber = message.ballotnumber
                replymessage = Message(type=MSG_ACCEPT,source=self.toPeer.serialize(),ballotnumber=self.ballotnumber,givenpvalues=self.accepted)
            else:
                replymessage = Message(type=MSG_REJECT,source=self.toPeer.serialize(),ballotnumber=self.ballotnumber,givenpvalues=self.accepted)
            connection.send(replymessage)
        elif message.type == MSG_PROPOSE:
            if message.ballotnumber >= self.ballotnumber:
                self.ballotnumber = message.ballotnumber
                newpvalue = PValue(ballotnumber=message.ballotnumber,commandnumber=message.commandnumber,proposal=message.proposal)
                self.accepted.append(newpvalue)
                replymessage = Message(type=MSG_ACCEPT,source=self.toPeer.serialize(),ballotnumber=self.ballotnumber,commandnumber=newpvalue.commandnumber)
            else:
                replymessage = Message(type=MSG_REJECT,source=self.toPeer.serialize(),ballotnumber=self.ballotnumber,commandnumber=newpvalue.commandnumber)
            connection.send(replymessage)
#        print "DEBUG: Closing the connection for %s:%d" % (addr,port)    
        connection.close()

    def cmd_paxos(self, args):
        for accepted in self.accepted:
            print accepted
        
'''main'''
def main():
    theAcceptor = Acceptor()
    theAcceptor.startservice()

'''run'''
if __name__=='__main__':
    main()

  


    
