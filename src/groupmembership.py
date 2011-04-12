import socket
import select
from optparse import OptionParser
from threading import Thread, Timer

from utils import *
from enums import *
from node import Node, options
from replica import *
from dnsquery import DNSQuery, DNSPacket

class Nameserver(Replica):
    """Nameserver keeps track of the connectivity state of the system and replies to
    QUERY messages from dnsserver."""
    def __init__(self):
        Replica.__init__(self, nodetype=NODE_NAMESERVER, port=5000, bootstrap=options.bootstrap)
        self.name = 'herbivore'
        self.registerednames = {'paxi':'127.0.0.1:5000'} # <name:nameserver> mappings
        self.nameserverconnections = {}  # <nameserver:connection> mappings

        self.udpport = 53 #DNS port: 53
        self.udpsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        try:
            self.udpsocket.bind((self.addr,self.udpport))
        except socket.error as e:
            print e
            print "Can't bind to UDP socket.."

    def startservice(self):
        """Starts the background services associated with a node."""
        Node.startservice(self)
        # Start a thread for the UDP server
        UDP_server_thread = Thread(target=self.udp_server_loop)
        UDP_server_thread.start()

    def performcore(self, msg, slotno, dometaonly=False):
        """The core function that performs a given command in a slot number. It 
        executes regular commands as well as META-level commands (commands related
        to the managements of the Paxos protocol) with a delay of WINDOW commands."""
        print "---> SlotNo: %d Command: %s DoMetaOnly: %s" % (slotno, self.decisions[slotno], dometaonly)
        command = self.decisions[slotno]
        commandlist = command.command.split()
        commandname = commandlist[0]
        commandargs = commandlist[1:]
        ismeta = (commandname in METACOMMANDS)
        noop = (commandname == "noop")        
        try:
            if dometaonly and ismeta:
                # execute a metacommand when the window has expired
                method = getattr(self, commandname)
                givenresult = method(commandargs)
            elif dometaonly and not ismeta:
                return
            elif not dometaonly and ismeta:
                # meta command, but the window has not passed yet, 
                # so just mark it as executed without actually executing it
                # the real execution will take place when the window has expired
                self.executed[self.decisions[slotno]] = META
                return
            elif not dometaonly and not ismeta:
                # this is the workhorse case that executes most normal commands
                givenresult = "NOTMETA"
        except AttributeError:
            print "command not supported: %s" % (command)
            givenresult = 'COMMAND NOT SUPPORTED'
        self.executed[self.decisions[slotno]] = givenresult

    def perform(self, msg):
        """Take a given PERFORM message, add it to the set of decided commands, and call performcore to execute."""
        if msg.commandnumber not in self.decisions:
            self.decisions[msg.commandnumber] = msg.proposal
        else:
            print "This commandnumber has been decided before.."
            
        while self.decisions.has_key(self.nexttoexecute):
            if self.decisions[self.nexttoexecute] in self.executed:
                logger("skipping command %d." % self.nexttoexecute)
                self.nexttoexecute += 1
            elif self.decisions[self.nexttoexecute] not in self.executed:
                logger("executing command %d." % self.nexttoexecute)

                # check to see if there was a meta command precisely WINDOW commands ago that should now take effect
                if self.nexttoexecute > WINDOW:
                    self.performcore(msg, self.nexttoexecute - WINDOW, True)
                self.performcore(msg, self.nexttoexecute)
                self.nexttoexecute += 1

    def msg_perform(self, conn, msg):
        """received a PERFORM message, perform it"""
        self.perform(msg)
        
    # DNS Side
    def udp_server_loop(self):
        while self.alive:
            try:
                print "Waiting..."
                inputready,outputready,exceptready = select.select([self.udpsocket],[],[self.udpsocket])
                for s in exceptready:
                    print "EXCEPTION ", s
                for s in inputready:
                    data,clientaddr = self.udpsocket.recvfrom(UDPMAXLEN)
                    logger("received a message from address %s" % str(clientaddr))
                    self.handle_query(data,clientaddr)
            except KeyboardInterrupt, EOFError:
                os._exit(0)
        self.udpsocket.close()
        return

    def handle_query(self, data, addr):
        dnsmsg = DNSPacket(data)
        query = dnsmsg.query
        serializedgroups = ""
        for group in self.groups.itervalues():
            serializedgroups += group.serialize()
        peers = serializedgroups.split()
        if query.domain == self.name:
            response = query.create_a_response(peers, auth=True)
            self.udpsocket.sendto(response, addr)
        elif self.registerednames.has_key(query.domain):
            response = query.create_ns_response(self.registerednames[query.domain])
            self.udpsocket.sendto(response, addr)
        else:
            response = query.create_error_response(self.addr)
            self.udpsocket.sendto(response, addr)

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
