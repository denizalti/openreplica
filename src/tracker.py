import socket
import select
from threading import Thread, Timer

from utils import *
from enums import *
from replica import *
from node import *

class Tracker(Replica):
    """Tracker keeps track of the connectivity state of the system"""
    def __init__(self, nodetype=NODE_TRACKER, port=None,  bootstrap=None):
        Replica.__init__(self, nodetype=nodetype, port=5010, bootstrap=options.bootstrap)
        
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
            logger("Sending Update Message to ", msg.source)
            self.send(updatemessage, peer=msg.source)

def main():
    membershipnode = Tracker()
    membershipnode.startservice()

if __name__=='__main__':
    main()
