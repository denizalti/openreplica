'''
@author: denizalti
@note: The Client
'''
from optparse import OptionParser
from threading import Thread, Lock, Condition
from node import Node
from enums import *
from communicationutils import scoutReply,commanderReply
from connection import ConnectionPool
from group import Group
from peer import Peer
from message import ClientMessage,Message,PaxosMessage,HandshakeMessage,PValue,PValueSet

class Client(Node):
    def __init__(self,accountid=0):
        Node.__init__(self, NODE_CLIENT)

    def startclient(self):
        # Start a thread that waits for inputs
        input_thread = Thread(target=self.getInputs)
        input_thread.start()

    def cmd_debit(self,args):
        clientmessage = ClientMessage(MSG_CLIENTREQUEST,self.me,'debit %s'%self.id)
        replymessage = self.server.sendWaitReply(self,clientmessage)
        if replymessage.proposal == "SUCCESS":
            print "Transaction performed.."
        elif replymessage.proposal == "FAIL":
            print "Transaction failed.."      
    
    def cmd_deposit(self,args):
        clientmessage = Message(type=MSG_CLIENTREQUEST,source=self.toPeer.serialize(),proposal='deposit %s'%self.id)
        replymessage = Message(self.bootstrap.sendWaitReply(clientmessage))
        if replymessage.type == MSG_SUCCESS:
            print "Transaction performed.."
        elif replymessage.type == MSG_FAIL:
            print "Transaction failed.."   
            
    def cmd_balance(self,args):
        clientmessage = Message(type=MSG_CLIENTREQUEST,source=self.toPeer.serialize(),proposal='balance %s'%self.id)
        replymessage = Message(self.bootstrap.sendWaitReply(clientmessage))
        if replymessage.type == MSG_SUCCESS:
            print "Balance is $%.2f"
        elif replymessage.type == MSG_FAIL:
            print "Request failed.." 
        
    def cmd_openaccount(self,args):
        clientmessage = Message(type=MSG_CLIENTREQUEST,source=self.toPeer.serialize(),proposal='openaccount %s'%self.id)
        replymessage = Message(self.bootstrap.sendWaitReply(clientmessage))
        if replymessage.type == MSG_SUCCESS:
            print "Request successful.."
        elif replymessage.type == MSG_FAIL:
            print "Request failed.." 
    
    def cmd_closeaccount(self,args):
        clientmessage = Message(type=MSG_CLIENTREQUEST,source=self.toPeer.serialize(),proposal='closeaccount %s'%self.id)
        replymessage = Message(self.bootstrap.sendWaitReply(clientmessage))
        if replymessage.type == MSG_SUCCESS:
            print "Request successful.."
        elif replymessage.type == MSG_FAIL:
            print "Request failed.." 
        
'''main'''
def main():
    theClient = Client()
    theClient.startclient()

'''run'''
if __name__=='__main__':
    main()

  


    
