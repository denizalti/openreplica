import socket
import select
from threading import Thread, Timer
import signal

from utils import *
from enums import *
from replica import *
from node import *

class Coordinator(Replica):
    """Coordinator keeps track of failures, it sends PING messages periodically and takes failed nodes
    out of the configuration"""
    def __init__(self):
        Replica.__init__(self, nodetype=NODE_COORDINATOR, port=5020, bootstrap=options.bootstrap)

        self.coordinatorcommandnumber = 1
        self.active = False
        self.ballotnumber = (0,self.id)
        self.outstandingprepares = {}
        self.outstandingproposes = {}
        self.clientpool = ConnectionPool()
        self.backoff = 0
        backoff_thread = Thread(target=self.update_backoff)
        backoff_event.clear()
        backoff_thread.start()

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

        if not self.stateuptodate:
            if msg.commandnumber == 1:
                self.stateuptodate = True
                return
            updatemessage = UpdateMessage(MSG_UPDATE, self.me)
            print "Sending Update Message to ", msg.source
            self.send(updatemessage, peer=msg.source)
   
    def startservice(self):
        """Starts the background services associated with a node
        and the periodic ping thread."""
        Replica.startservice(self)
        # Start a thread for periodic pings
        ping_thread = Thread(target=self.periodic_ping)
        ping_thread.start()
        # Start a thread for periodic clean-ups
        coordinate_thread = Thread(target=self.coordinate)
        coordinate_thread.start()

    def periodic_ping(self):
        while True:
            checkliveness = set()
            for type,group in self.groups.iteritems():
                checkliveness = checkliveness.union(group.members)
            helomessage = HandshakeMessage(MSG_HELO, self.me)
            for pingpeer in checkliveness:
                try:
                    self.send(helomessage, peer=pingpeer)
                    logger("PING to %s." %str(pingpeer))
                except:
                    print "WHOOPS."
                    # take this node out of the configuration
                    deletecommand = self.create_delete_command(pingpeer)
                    logger("initiating a new coordination command")
                    self.do_command_prepare(deletecommand)

            time.sleep(ACKTIMEOUT)

    def coordinate(self):
        """Decide which node should be removed and issue the command."""
        while True:
            print "*** COORDINATE ***"
            peerstoremove = set()
            with self.outstandingmessages_lock:
                for id, messageinfo in self.outstandingmessages.iteritems():
                    now = time.time()
                    if messageinfo.messagestate == ACK_NOTACKED and (messageinfo.timestamp - LIVENESSTIMEOUT) > now:
                        peerstoremove.add(messageinfo.destination)

            for peertoremove in peerstoremove:
                print str(peertoremove)
                # take this node out of the configuration
                deletecommand = self.create_delete_command(peertoremove)
                logger("initiating a new coordination command")
                self.do_command_prepare(deletecommand)

            time.sleep(LIVENESSTIMEOUT)

    def create_delete_command(self, node):
        mynumber = self.coordinatorcommandnumber
        self.coordinatorcommandnumber += 1
        nodetype = node_names[node.type].lower()
        operation = "del_%s %s:%d" % (nodetype, node.addr, node.port)
        command = Command(self.me, mynumber, operation)
        return command

    def create_add_command(self, node):
        mynumber = self.coordinatorcommandnumber
        self.coordinatorcommandnumber += 1
        nodetype = node_names[node.type].lower()
        operation = "add_%s %s:%d" % (nodetype, node.addr, node.port)
        command = Command(self.me, mynumber, operation)
        return command
        
def main():
    coordinatornode = Coordinator()
    coordinatornode.startservice()
    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()

if __name__=='__main__':
    main()
