import socket
import select
from threading import Thread, Timer

from utils import *
from enums import *
from replica import *
from node import *

class Coordinator(Tracker):
    """Coordinator keeps track of failures, it sends PING messages periodically and takes failed nodes
    out of the configuration"""
    def __init__(self):
        Tracker.__init__(self, nodetype=NODE_COORDINATOR, port=5020, bootstrap=options.bootstrap)
        
    def startservice(self):
        """Starts the background services associated with a node
        and the periodic ping thread."""
        Tracker.startservice(self)
        # Start a thread for periodic pings
        ping_thread = Thread(target=self.periodic_ping)
        ping_thread.start()
        # Start a thread for periodic clean-ups
        coordinate_thread = Thread(target=self.coordinate)
        coordinate_thread.start()

    def periodic_ping(self):
        for group in self.groups:
            for peer in group:
                logger("sending PING to %s" % pingpeer)
                helomessage = HandshakeMessage(MSG_HELO, self.me)
                self.send(helomessage, peer=pingpeer)

    def coordinate(self):
        while True:
            checkliveness = set()
            for type,group in self.groups.iteritems():
                checkliveness = checkliveness.union(group.members)

            try:
                with self.outstandingmessages_lock:
                    for id, messageinfo in self.outstandingmessages.iteritems():
                        now = time.time()
                        if messageinfo.messagestate == ACK_ACKED \
                               and (messageinfo.timestamp + LIVENESSTIMEOUT) < now \
                               and messageinfo.destination in checkliveness:
                            checkliveness.remove(messageinfo.destination)
            except Exception as ec:
                logger("exception in resend: %s" % ec)
                
            if DO_PERIODIC_PINGS:
                for pingpeer in checkliveness:
                    logger("sending PING to %s" % pingpeer)
                    helomessage = HandshakeMessage(MSG_HELO, self.me)
                    self.send(helomessage, peer=pingpeer)

            time.sleep(ACKTIMEOUT/5)
        
        

def main():
    coordinatornode = Coordinator()
    coordinator.startservice()

if __name__=='__main__':
    main()
