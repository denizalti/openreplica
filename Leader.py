'''
@author: denizalti
@note: The Leader
'''
from optparse import OptionParser
import threading
from Utils import *
from Connection import *
from Group import *
from Peer import *
from Message import *
from Acceptor import *
from Scout import *
from Commander import *

parser = OptionParser(usage="usage: %prog -i id -p port -b bootstrap")
parser.add_option("-i", "--id", action="store", dest="id", help="node id")
parser.add_option("-p", "--port", action="store", dest="port", help="port for the node")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port:id triple for the peer")
(options, args) = parser.parse_args()

# TIMEOUT THREAD
class Leader():
    def __init__(self, id, port, bootstrap=None):
        print "port: ", port
        print "id: ", id
        print "bootstrap: ", bootstrap
        self.addr = findOwnIP()
        self.port = int(port)
        self.id = int(id)
        self.toPeer = Peer(self.id,self.addr,self.port)
        # groups
        self.acceptors = Group()
        self.replicas = Group()
        self.leaders = Group()
        # print some information
        print "DEBUG: IP: %s Port: %d ID: %d" % (self.addr,self.port,self.id)
        if bootstrap:
            bootaddr,bootport,bootid = bootstrap.split(":")
            bootpeer = Peer(int(bootid),int(bootport),bootaddr)
            helomsg = self.create_helo('')
            self.neighborhoodSet.send_to_peer(bootpeer,helomsg)
        
        # Synod Leader State
        self.ballotnumber = (self.id,0)
        self.pvalues = [] # array of pvalues
    
    def incrementBallotnumber(self):
        self.ballotnumber[1] += 1
    
    def newCommand(self,commandnumber,proposal):
        replyFromScout = scoutReply()
        replyFromCommander = commanderReply()
        chosenpvalue = pvalue(self.ballotnumber,commandnumber,proposal)
        scout = Scout(self.toPeer,self.acceptors,self.ballotnumber,replyFromScout)
        scout.start()
        # This is a busy-wait, should be optimized
        # Need Locks for Replies.
        while replyFromScout.type != 0 or replyFromCommander.type != 0:
            if replyFromScout.type != 0:
                if replyFromScout.type == SCOUT_ADOPTED:
                    possiblepvalues = []
                    for pvalue in replyFromScout.pvalues:
                        if pvalue.commandnumber == commandnumber:
                            possiblepvalues.append(pvalue)
                    if len(possiblepvalues) > 0:
                        chosenpvalue = max(possiblepvalues)
                    replyFromCommander = commanderReply()
                    commander = Commander(self.toPeer,self.acceptors,self.ballotnumber,chosenpvalue,replyFromCommander)
                    commander.start()
                    continue
                elif replyFromScout.type == SCOUT_PREEMPTED:
                    if replyFromScout.ballotnumber > self.ballotnumber:
                        self.incrementBallotnumber()
                        replyFromScout = scoutReply()
                        scout = Scout(self.toPeer,self.acceptors,self.ballotnumber,replyFromScout)
                        scout.start()

            elif replyFromCommander.type != 0:
                if replyFromCommander.type == COMMANDER_CHOSEN:
                    message = Message(type=MSG_PERFORM,source=self.leader.serialize,commandnumber=replyFromCommander[1],proposal=proposal)
                    self.replicas.broadcast(message)
                    break
                elif replyFromCommander.type == COMMANDER_PREEMPTED:
                    if replyFromScout.ballotnumber > self.ballotnumber:
                        self.incrementBallotnumber()
                        replyFromScout = scoutReply()
                        scout = Scout(self.toPeer,self.acceptors,self.ballotnumber,replyFromScout)
                        scout.start()

            else:
                print "DEBUG: Shouldn't reach here.."
        
   
'''main'''
def main():
    if options.bootstrap:
        theNode = Leader(options.id,options.port,options.bootstrap)
    else:
        theNode = Leader(options.id,options.port)

'''run'''
if __name__=='__main__':
    main()

  


    
