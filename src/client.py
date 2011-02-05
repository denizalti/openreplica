'''
@author: denizalti
@note: The Client connects to a Leader and makes requests.
@date: February 1, 2011
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

    #XXX: All these functions have to be checked..
    def cmd_deposit(self,args):
        clientmessage = ClientMessage(MSG_CLIENTREQUEST,self.me,'deposit %s'%self.id)
        replymessage = self.server.sendWaitReply(self,clientmessage)
        if replymessage.proposal == "SUCCESS":
            print "Transaction performed.."
        elif replymessage.proposal == "FAIL":
            print "Transaction failed.."    
            
    def cmd_balance(self,args):
        clientmessage = ClientMessage(MSG_CLIENTREQUEST,self.me,'balance %s'%self.id)
        replymessage = self.server.sendWaitReply(self,clientmessage)
        if replymessage.proposal == "FAIL":
            print "Request failed.."
        else:
            print "Balance is $%.2f" % replymessage.proposal
        
    def cmd_openaccount(self,args):
        clientmessage = ClientMessage(MSG_CLIENTREQUEST,self.me,'openaccount %s'%self.id)
        replymessage = self.server.sendWaitReply(self,clientmessage)
        if replymessage.proposal == "SUCCESS":
            print "Transaction performed.."
        elif replymessage.proposal == "FAIL":
            print "Request failed.."  
    
    def cmd_closeaccount(self,args):
        clientmessage = ClientMessage(MSG_CLIENTREQUEST,self.me,'closeaccount %s'%self.id)
        replymessage = self.server.sendWaitReply(self,clientmessage)
        if replymessage.proposal == "SUCCESS":
            print "Request successful.."
        elif replymessage.proposal == "FAIL":
            print "Request failed.."  
        
'''main'''
def main():
    theClient = Client()
    theClient.startclient()

'''run'''
if __name__=='__main__':
    main()

  


    
