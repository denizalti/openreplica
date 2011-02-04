'''
@author: denizalti
@note: The Client
'''
from optparse import OptionParser
from threading import Thread, Lock, Condition
from enums import *
from utils import *
from communicationutils import *
from connection import *
from group import *
from peer import *
from message import *
from bank import *

parser = OptionParser(usage="usage: %prog -p port -b bootstrap")
parser.add_option("-p", "--port", action="store", dest="port", help="port for the node")
parser.add_option("-b", "--bootstrap", action="store", dest="bootstrap", help="address:port tuple for the bootstrap")
parser.add_option("-i", "--id", action="store", dest="id", type="int", default=0, help="[optional] id for the account")
(options, args) = parser.parse_args()

# TIMEOUT THREAD
class Client():
    def __init__(self,port,bootstrap,accountid):
        self.addr = findOwnIP()
        self.port = int(port)
        if accountid == 0:
            self.accountid = createID(self.addr,self.port)
        else:
            self.accountid = accountid
        self.type = NODE_CLIENT
        self.toPeer = Peer(self.accountid,self.addr,self.port,self.type)
        # Exit
        self.run = True 
        # print some information
        print "Client of Account %d: %s:%d" % (self.accountid,self.addr,self.port)
        if bootstrap:
            bootaddr,bootport = bootstrap.split(":")
            bootid = createID(bootaddr,bootport)
            self.bootstrap = Peer(bootid,bootaddr,int(bootport))
            heloMessage = Message(type=MSG_HELO,source=self.toPeer.serialize())
            self.bootstrap.send(heloMessage)
        else:
            print "Client needs a server to connect.."
        # Start a thread with the server which will start a thread for each request
#        server_thread = Thread(target=self.serverLoop)
#        server_thread.start()
        # Start a thread that waits for inputs
        input_thread = Thread(target=self.getInputs)
        input_thread.start()
        
    def __str__(self):
        returnstr = "Client Information\n"
        returnstr += "IP: %s\n" % self.addr
        returnstr += "Port: %d\n" % self.port
        return returnstr
        
    def serverLoop(self):
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        s.bind((self.addr,self.port))
        s.listen(10)
        while self.run:
            try:
                clientsock,clientaddr = s.accept()
                # Start a Thread
                Thread(target=self.handleConnection,args =[clientsock]).start()
            except KeyboardInterrupt:
                break
        s.close()
        return
        
    def handleConnection(self,clientsock):
        print "DEBUG: Handling the connection.."
        addr,port = clientsock.getpeername()
        connection = Connection(addr,port,reusesock=clientsock)
        message = Message(connection.receive())
        if message.type == MSG_DONE:
            print "Transaction performed."
        elif message.type == MSG_FAIL:
            print "Transaction failed.."      
        connection.close()
        
    def debit(self):
        clientmessage = Message(type=MSG_CLIENTREQUEST,source=self.toPeer.serialize(),proposal='debit %s'%self.accountid)
        replymessage = Message(self.bootstrap.sendWaitReply(clientmessage))
        if replymessage.type == MSG_SUCCESS:
            print "Transaction performed.."
        elif replymessage.type == MSG_FAIL:
            print "Transaction failed.."      
    
    def deposit(self):
        clientmessage = Message(type=MSG_CLIENTREQUEST,source=self.toPeer.serialize(),proposal='deposit %s'%self.accountid)
        replymessage = Message(self.bootstrap.sendWaitReply(clientmessage))
        if replymessage.type == MSG_SUCCESS:
            print "Transaction performed.."
        elif replymessage.type == MSG_FAIL:
            print "Transaction failed.."   
            
    def balance(self):
        clientmessage = Message(type=MSG_CLIENTREQUEST,source=self.toPeer.serialize(),proposal='balance %s'%self.accountid)
        replymessage = Message(self.bootstrap.sendWaitReply(clientmessage))
        if replymessage.type == MSG_SUCCESS:
            print "Balance is $%.2f"
        elif replymessage.type == MSG_FAIL:
            print "Request failed.." 
        
    def openaccount(self):
        clientmessage = Message(type=MSG_CLIENTREQUEST,source=self.toPeer.serialize(),proposal='open %s'%self.accountid)
        replymessage = Message(self.bootstrap.sendWaitReply(clientmessage))
        if replymessage.type == MSG_SUCCESS:
            print "Request successful.."
        elif replymessage.type == MSG_FAIL:
            print "Request failed.." 
    
    def closeaccount(self):
        clientmessage = Message(type=MSG_CLIENTREQUEST,source=self.toPeer.serialize(),proposal='close %s'%self.accountid)
        replymessage = Message(self.bootstrap.sendWaitReply(clientmessage))
        if replymessage.type == MSG_SUCCESS:
            print "Request successful.."
        elif replymessage.type == MSG_FAIL:
            print "Request failed.." 
        
    def getInputs(self):
        while self.run:
            input = raw_input("What should I do? ")
            if len(input) == 0:
                print "I'm listening.."
            else:
                input = input.split()
                input[0] = input[0].upper()
                if input[0] == 'HELP':
                    self.printHelp()
                elif input[0] == 'OPEN':
                    self.openaccount()
                elif input[0] == 'CLOSE':
                    self.closeaccount()
                elif input[0] == 'DEBIT':
                    self.debit()
                elif input[0] == 'DEPOSIT':
                    self.deposit()
                elif input[0] == 'BALANCE':
                    self.balance()
                elif input[0] == 'EXIT':
                    print "So long and thanks for all the fish.."
                    self.die()
                else:
                    print "Sorry I couldn't get it.."
        return
                    
    def die(self):
        self.run = False
        byeMessage = Message(type=MSG_BYE,source=self.toPeer.serialize())
        self.bootstrap.send(byeMessage)
        self.toPeer.send(byeMessage)
                    
    def printHelp(self):
        print "To open an account type OPEN"
        print "To debit 10% of the account type DEBIT"
        print "To deposit 10% of the account type DEPOSIT"
        print "To see the balance of the account type BALANCE"
        print "To close an account type CLOSE"
        print "For help type HELP"
        print "To exit type EXIT"
   
'''main'''
def main():
    theClient = Client(options.port,options.bootstrap,options.id)

'''run'''
if __name__=='__main__':
    main()

  


    
