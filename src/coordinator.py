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
    def __init__(self,instantiateobj=False):
        Replica.__init__(self, nodetype=NODE_COORDINATOR, instantiateobj=instantiateobj, port=5020, bootstrap=options.bootstrap)

        self.coordinatorcommandnumber = 1
        self.active = False
        self.ballotnumber = (0,self.id)
        self.outstandingprepares = {}
        self.outstandingproposes = {}
        self.clientpool = ConnectionPool()
        self.commandgap = 1
        self.backoff = 0
        backoff_thread = Thread(target=self.update_backoff)
        backoff_event.clear()
        backoff_thread.start()

    def performcore(self, msg, slotnumber, dometaonly=False, designated=False):
        """The core function that performs a given command in a slot number. It 
        executes regular commands as well as META-level commands (commands related
        to the managements of the Paxos protocol) with a delay of WINDOW commands."""
        print "---> SlotNo: %d Command: %s DoMetaOnly: %s" % (slotnumber, self.decisions[slotnumber], dometaonly)
        command = self.decisions[slotnumber]
        commandlist = command.command.split()
        commandname = commandlist[0]
        commandargs = commandlist[1:]
        ismeta = (commandname in METACOMMANDS)
        noop = (commandname == "noop")        
        try:
            if dometaonly and ismeta:
                # execute a metacommand when the window has expired
                method = getattr(self, commandname)
                givenresult = method(*commandargs)
            elif dometaonly and not ismeta:
                return
            elif not dometaonly and ismeta:
                # meta command, but the window has not passed yet, 
                # so just mark it as executed without actually executing it
                # the real execution will take place when the window has expired
                self.executed[self.decisions[slotnumber]] = META
                return
            elif not dometaonly and not ismeta:
                # this is the workhorse case that executes most normal commands
                givenresult = "NOTMETA"
        except AttributeError:
            print "command not supported: %s" % (command)
            givenresult = 'COMMAND NOT SUPPORTED'
        self.executed[self.decisions[slotnumber]] = givenresult

    def perform(self, msg, designated=False):
        if msg.commandnumber not in self.decisions:
            self.add_to_decisions(msg.commandnumber, msg.proposal)
        # If replica was using this commandnumber for a different proposal, initiate it again
        if self.proposals.has_key(msg.commandnumber) and msg.proposal != self.proposals[msg.commandnumber]:
            self.do_command_propose(self.proposals[msg.commandnumber])
            
        while self.decisions.has_key(self.nexttoexecute):
            requestedcommand = self.decisions[self.nexttoexecute]
            if requestedcommand in self.executed:
                logger("previously executed command %d." % self.nexttoexecute)
                self.nexttoexecute += 1
                # the window just got bumped by one
                # check if there are pending commands, and issue one of them
                self.issue_pending_command(self.nexttoexecute)
            elif requestedcommand not in self.executed:
                logger("executing command %d." % self.nexttoexecute)
                # check to see if there was a meta command precisely WINDOW commands ago that should now take effect
                # We are calling performcore 2 times, the timing gets screwed plus this is very unefficient :(
                if self.nexttoexecute > WINDOW:
                    self.performcore(msg, self.nexttoexecute - WINDOW, True, designated=designated)
                self.performcore(msg, self.nexttoexecute, designated=designated)
                self.nexttoexecute += 1
                # the window just got bumped by one
                # check if there are pending commands, and issue one of them
                self.issue_pending_command(self.nexttoexecute)
                
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
            pingmessage = HandshakeMessage(MSG_PING, self.me)
            for pingpeer in checkliveness:
                try:
                    self.send(pingmessage, peer=pingpeer)
                    #logger("PING to %s." %str(pingpeer))
                except:
                    print "WHOOPS."
                    # take this node out of the configuration
                    deletecommand = self.create_delete_command(pingpeer)
                    logger("initiating a new coordination command")
                    self.do_command_prepare(deletecommand)
            time.sleep(ACKTIMEOUT)

    def coordinate(self):
        while True:
            peerstoremove = set()
            with self.outstandingmessages_lock:
                for id, messageinfo in self.outstandingmessages.iteritems():
                    now = time.time()
                    if messageinfo.messagestate == ACK_NOTACKED and (messageinfo.timestamp - LIVENESSTIMEOUT) > now:
                        peerstoremove.add(messageinfo.destination)
            for peertoremove in peerstoremove:
                # take this node out of the configuration
                deletecommand = self.create_delete_command(peertoremove)
                logger("initiating a new coordination command to remove %s" % peertoremove)
                self.do_command_prepare(deletecommand)
            time.sleep(LIVENESSTIMEOUT)

    def msg_helo(self, conn, msg):
        addcommand = self.create_add_command(msg.source)
        logger("initiating a new coordination command to add %s" % msg.source)
        self.do_command_prepare(addcommand)

    def msg_refer(self, conn, msg):
        """A peer is referred by its bootstrap node"""
        logger("Got a referral for %s from %s" %(msg.referredpeer, msg.source))
        if msg.referredpeer == self.me:
            return
        addcommand = self.create_add_command(msg.referredpeer)
        self.do_command_prepare(addcommand)

    def terminate_handler(self, signal, frame):
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)
        
def main():
    coordinatornode = Coordinator()
    coordinatornode.startservice()
    signal.signal(signal.SIGINT, coordinatornode.interrupt_handler)
    signal.signal(signal.SIGTERM, coordinatornode.terminate_handler)
    signal.pause()

if __name__=='__main__':
    main()
