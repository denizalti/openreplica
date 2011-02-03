'''
@author: denizalti
@note: The Client
'''
from optparse import OptionParser
from threading import Thread, Lock, Condition
from utils import *
from communicationutils import *
from connection import *
from group import *
from peer import *
from message import *
from bank import *

parser = OptionParser(usage="usage: %prog -p port -s server")
parser.add_option("-p", "--port", action="store", dest="port", help="port for the node")
parser.add_option("-s", "--server", action="store", dest="server", help="address:port tuple for the server")
(options, args) = parser.parse_args()

# TIMEOUT THREAD
class Client():
    def __init__(self, id, port, bootstrap):
        self.addr = findOwnIP()
        self.port = int(port)
        self.id = createID(self.addr,self.port)
        self.type = CLIENT
        self.toPeer = Peer(self.id,self.addr,self.port,self.type)
        # Exit
        self.run = True 
        # print some information
        print "DEBUG: IP: %s Port: %d ID: %d" % (self.addr,self.port,self.id)
        if bootstrap:
            bootaddr,bootport = bootstrap.split(":")
            bootid = createID(bootaddr,bootport)
            self.server = Peer(bootid,bootaddr,int(bootport))
            heloMessage = Message(type=MSG_HELO,source=self.toPeer.serialize())
            self.server.send(heloMessage)
        else:
            print "Client needs a server to connect.."
        # Start a thread with the server which will start a thread for each request
        server_thread = Thread(target=self.serverLoop)
        server_thread.start()
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
        tuple = addr+":"+str(port)
        print tuple
        connection = Connection(addr,port,reusesock=clientsock)
        message = Message(connection.receive())
        if message.type == MSG_DONE:
            print "Transaction performed."
        elif message.type == MSG_FAIL:
            print "Transaction failed.."      
        connection.close()
        
    def debitTen(self):
        debitMessage = Message(type=MSG_DEBIT,source=self.toPeer.serialize())
        debitReply = Message(self.server.sendWaitReply(debitMessage))
        if debitReply.type == MSG_DONE:
            print "Transaction performed."
        elif debitReply.type == MSG_FAIL:
            print "Transaction failed.."      
    
    def depositTen(self):
        depositMessage = Message(type=MSG_DEPOSIT,source=self.toPeer.serialize())
        depositReply = Message(self.server.sendWaitReply(depositMessage))
        if depositReply.type == MSG_DONE:
            print "Transaction performed."
        elif depositReply.type == MSG_FAIL:
            print "Transaction failed.." 
            
    def checkBalance(self):
        balanceMessage = Message(type=MSG_BALANCE,source=self.toPeer.serialize())
        balanceReply = Message(self.server.sendWaitReply(balanceMessage))
        print "The balance is $%d\n" % balanceReply.balance
        
    def openAccount(self):
        pass
    
    def closeAccount(self):
        pass
        
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
                elif input[0] == 'DEBIT':
                    self.debitTen()
                elif input[0] == 'DEPOSIT':
                    self.depositTen()
                elif input[0] == 'BALANCE':
                    self.checkBalance()
                elif input[0] == 'EXIT':
                    print "So long and thanks for all the fish.."
                    self.die()
                else:
                    print "Sorry I couldn't get it.."
        return
                    
    def die(self):
        self.run = False
        byeMessage = Message(type=MSG_BYE,source=self.toPeer.serialize())
        self.server.send(byeMessage)
        self.toPeer.send(byeMessage)
                    
    def printHelp(self):
        print "To open an account type OPEN"
        print "To debit 10% of the account type DEBIT AccountID"
        print "To deposit 10% of the account type DEPOSIT AccountID"
        print "To see the balance of the account type BALANCE AccountID"
        print "To close an account type CLOSE AccountID"
        print "For help type HELP"
        print "To exit type EXIT"
   
'''main'''
def main():
    theClient = Client(options.port,options.server)

'''run'''
if __name__=='__main__':
    main()

  


    
