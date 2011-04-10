from optparse import OptionParser
from threading import Thread, Timer

from node import Node, options
from enums import NODE_NAMESERVER, ACKTIMEOUT

class Nameserver(Node):
    """Nameserver keeps track of the connectivity state of the system and replies to
    QUERY messages from dnsserver."""
    def __init__(self):
        Node.__init__(self, NODE_NAMESERVER, port=5000,  bootstrap=options.bootstrap)

    def startservice(self):
        """Starts the background services associated with a node."""
        # Start a thread with the server which will start a thread for each request
        server_thread = Thread(target=self.server_loop)
        server_thread.start()
        print "YAAAYYY..."
        # Start a thread that pings neighbors
        timer_thread = Timer(ACKTIMEOUT/5, self.periodic)
        timer_thread.start()

# nameserver query function
    def msg_query(self, conn, msg):
        """Send groups as a reply to the query msg"""
        serializedgroups = ""
        for group in self.groups:
            serializedgroups += group.serialize()
        queryreplymessage = HandshakeMessage(MSG_QUERYREPLY, self.me, serializedgroups)
        self.send(queryreplymessage, peer=msg.source)

def main():
    nameservernode = Nameserver()
    nameservernode.startservice()

if __name__=='__main__':
    main()
