'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: The Replica keeps an object and responds to Perform messages received from the Leader.
@copyright: See LICENSE
'''
import inspect
import math, random, time
import os, sys
import signal
from threading import Thread, Lock, Condition, Timer, Event
from concoord.peer import Peer
from concoord.group import Group
from concoord.command import Command
from concoord.pvalue import PValue, PValueSet
from concoord.responsecollector import ResponseCollector
from concoord.connection import Connection, ConnectionPool
from concoord.exception import ConCoordException, BlockingReturn, UnblockingReturn
from concoord.node import *
from concoord.enums import *
from concoord.utils import *
from concoord.message import *

backoff_event = Event()
class Replica(Node):
    def __init__(self,
                 nodetype=NODE_REPLICA,
                 instantiateobj=True,
                 port=None,
                 bootstrap=None):
        Node.__init__(self, nodetype, instantiateobj=instantiateobj)
        # load and initialize the object to be replicated
        if instantiateobj:
            self.object = None
            for objectloc in ['concoord.'+self.objectfilename[:-3],
                              'concoord.object.'+self.objectfilename[:-3],
                              'concoord.test.'+self.objectfilename[:-3],
                              self.objectfilename[:-3]]:
                try:
                    ip = objectloc.split('.')
                    mod = __import__(objectloc, {}, {}, [])
                    for module in ip[1:]:
                        mod = getattr(mod, module, None)
                    if hasattr(mod, self.objectname):
                        self.object = getattr(mod, self.objectname)()
                        break
                except ImportError as e:
                    continue
                except AttributeError as e:
                    continue
            if self.object == None:
                self.logger.write("Object Error", "Object cannot be found.")
                self._graceexit(1)
            else:
                try:
                    self.token = getattr(self.object, '_%s__concoord_token' % self.objectname)
                except:
                    self.token = None
        # leadership
        self.leader_initializing = False
        self.isleader = False
        self.nexttoexecute = 1
        # decided commands: <commandnumber:command>
        self.decisions = {}
        self.decisionset = set()
        # executed commands: <command:(replycode,commandresult,unblocked{})>
        self.executed = {}
        # commands that are proposed: <commandnumber:command>
        self.proposals = {}
        self.proposalset = set()
        # commands that are received, not yet proposed: <commandnumber:command>
        self.pendingcommands = {}
        self.pendingcommandset = set()
        # commandnumbers known to be in use
        self.usedcommandnumbers = set()
        # number for metacommands initiated from this replica
        self.metacommandnumber = 0
        self.clientpool = ConnectionPool()

        # PERFORMANCE MEASUREMENT VARS
        self.firststarttime = 0
        self.firststoptime = 0
        self.secondstarttime = 0
        self.secondstoptime = 0
        self.count = 0

        self.throughput_runs = 0
        self.throughput_stop = 0
        self.throughput_start = 0
        
    def __str__(self):
        rstr = "%s %s:%d\n" % ("LEADER" if self.isleader else node_names[self.type], self.addr, self.port)
        rstr += "Waiting to execute command %d.\n" % self.nexttoexecute
        rstr += "Commands:\n"
        for commandnumber, command in self.decisions.iteritems():
            state = ''
            if self.executed.has_key(command):
                state = '\t' + cr_codes[self.executed[command][0]]+ '\t' + str(self.executed[command][1])
            rstr += str(commandnumber) + ":\t" + str(command) + state + '\n'
        if len(self.pendingcommands):
            rstr += "Pending Commands:\n"
            for commandnumber, command in self.pendingcommands.iteritems():
                rstr += str(commandnumber) + ":\t" + str(command) + '\n'
        if len(self.proposals):
            rstr += "Proposals:\n"
            for commandnumber, command in self.proposals.iteritems():
                rstr += str(commandnumber) + ":\t" + str(command) + '\n'
        return rstr

    def startservice(self):
        """Start the background services associated with a replica."""
        Node.startservice(self)
        leaderping_thread = Timer(LIVENESSTIMEOUT, self.ping_leader)
        leaderping_thread.name = 'LeaderPingThread'
        leaderping_thread.start()

    @staticmethod
    def _apply_args_to_method(method, args, _concoord_command):
        argspec = inspect.getargspec(method)
        if argspec.args and argspec.args[-1] == '_concoord_command':
            return method(*args, _concoord_command=_concoord_command)
        elif argspec.keywords is not None:
            return method(*args, _concoord_command=_concoord_command)
        else:
            return method(*args)

    def performcore(self, msg, slotnumber, dometaonly=False, designated=False):
        """The core function that performs a given command in a slot number. It 
        executes regular commands as well as META-level commands (commands related
        to the managements of the Paxos protocol) with a delay of WINDOW commands."""
        command = self.decisions[slotnumber]
        commandtuple = command.command
        if type(commandtuple) == str:
            commandname = commandtuple
            commandargs = []
        else:
            commandname = commandtuple[0]
            commandargs = commandtuple[1:]
        ismeta = (commandname in METACOMMANDS)
        noop = (commandname == "noop")
        send_result_to_client = True
        self.logger.write("State:", "---> SlotNumber: %d Command: %s DoMetaOnly: %s IsMeta: %s"
                          % (slotnumber, self.decisions[slotnumber], dometaonly, ismeta))
        # Result triple
        clientreplycode, givenresult, unblocked = (-1, None, {})
        try:
            if dometaonly and not ismeta:
                return
            elif noop:
                method = getattr(self, NOOP)
                clientreplycode = CR_OK
                givenresult = "NOOP"
                unblocked = {}
                send_result_to_client = False
            elif dometaonly and ismeta:
                # execute a metacommand when the window has expired
                self.logger.write("State", "commandname: %s args: %s" % (commandname, str(commandargs)))
                method = getattr(self, commandname)
                clientreplycode = CR_META
                givenresult = method(*commandargs)
                unblocked = {}
                send_result_to_client = False
            elif not dometaonly and ismeta:
                # meta command, but the window has not passed yet, 
                # so just mark it as executed without actually executing it
                # the real execution will take place when the window has expired
                self.add_to_executed(self.decisions[slotnumber], (CR_META, META, {}))
                return
            elif not dometaonly and not ismeta:
                # this is the workhorse case that executes most normal commands
                method = getattr(self.object, commandname)
                # Watch out for the lock release and acquire!
                self.lock.release()
                try:
                    givenresult = self._apply_args_to_method(method, commandargs, command)
                    clientreplycode = CR_OK
                    send_result_to_client = True
                except BlockingReturn as blockingretexp:
                    self.logger.write("State", "Blocking Client.")
                    givenresult = blockingretexp.returnvalue
                    clientreplycode = CR_BLOCK
                    send_result_to_client = True
                except UnblockingReturn as unblockingretexp:
                    self.logger.write("State", "Unblocking Client(s).")
                    # Get the information about the method call
                    # These will be used to update executed and
                    # to send reply message to the caller client
                    givenresult = unblockingretexp.returnvalue
                    unblocked = unblockingretexp.unblocked
                    clientreplycode = CR_OK
                    send_result_to_client = True
                    # If there are clients to be unblocked that have
                    # been blocked previously, send them unblock messages
                    for unblockedclientcommand in unblocked.iterkeys():
                        self.send_reply_to_client(CR_UNBLOCK, None, unblockedclientcommand)
                except Exception as e:
                    self.logger.write("Execution Error", "Error during method invocation: %s" % str(e))
                    givenresult = e
                    clientreplycode = CR_EXCEPTION
                    send_result_to_client = True
                    unblocked = {}
                self.lock.acquire()
        except (TypeError, AttributeError) as t:
            self.logger.write("Execution Error", "command not supported: %s" % (command))
            givenresult = 'Method Does Not Exist: ', commandname
            clientreplycode = CR_EXCEPTION
            unblocked = {}
            send_result_to_client = True
        self.add_to_executed(self.decisions[slotnumber], (clientreplycode,givenresult,unblocked))
        
        if commandname not in METACOMMANDS:
            # if this client contacted me for this operation, return him the response 
            if send_result_to_client and self.isleader and command.client.getid() in self.clientpool.poolbypeer.keys():
                self.send_reply_to_client(clientreplycode, givenresult, command)

        if slotnumber % GARBAGEPERIOD == 0 and self.isleader:
            mynumber = self.metacommandnumber
            self.metacommandnumber += 1
            garbagetuple = ("garbage_collect", slotnumber)
            garbagecommand = Command(self.me, mynumber, garbagetuple)
            if self.leader_initializing:
                self.handle_client_command(garbagecommand, prepare=True)
            else:
                self.handle_client_command(garbagecommand)
        self.logger.write("State:", "returning from performcore!")

    def send_reply_to_client(self, clientreplycode, givenresult, command):
        self.logger.write("State", "Sending REPLY to CLIENT")
        clientreply = ClientReplyMessage(MSG_CLIENTREPLY, self.me, reply=givenresult, replycode=clientreplycode, inresponseto=command.clientcommandnumber)
        self.logger.write("State", "Clientreply: %s\nAcceptors: %s" % (str(clientreply), str(self.groups[NODE_ACCEPTOR])))
        clientconn = self.clientpool.get_connection_by_peer(command.client)
        if clientconn == None or clientconn.thesocket == None:
            self.logger.write("State", "Client connection does not exist.")
            return
        clientconn.send(clientreply)

    def perform(self, msg, designated=False):
        """Take a given PERFORM message, add it to the set of decided commands, and call performcore to execute."""
        self.logger.write("State:", "Performing msg %s" % str(msg))
        if msg.commandnumber not in self.decisions:
            self.add_to_decisions(msg.commandnumber, msg.proposal)
        # If replica was using this commandnumber for a different proposal, initiate it again
        if self.proposals.has_key(msg.commandnumber) and msg.proposal != self.proposals[msg.commandnumber]:
            self.initiate_command(self.proposals[msg.commandnumber])
            
        while self.decisions.has_key(self.nexttoexecute):
            requestedcommand = self.decisions[self.nexttoexecute]
            if requestedcommand in self.executed:
                self.logger.write("State", "Previously executed command %d." % self.nexttoexecute)
                # If we are a leader, we should send a reply to the client for this command
                # in case the client didn't receive the reply from the previous leader
                if self.isleader:
                    prevrcode, prevresult, prevunblocked = self.executed[requestedcommand]
                    if prevrcode == CR_BLOCK:
                        # As dictionary is not sorted we have to start from the beginning every time
                        for resultset in self.executed.itervalues():
                            if resultset[UNBLOCKED] == requestedcommand:
                                # This client has been UNBLOCKED
                                prevresult = None
                                prevrcode = CR_UNBLOCK
                    self.logger.write("State", "Sending reply to client.")
                    self.send_reply_to_client(prevrcode, prevresult, requestedcommand)
                self.nexttoexecute += 1
                # the window just got bumped by one
                # check if there are pending commands, and issue one of them
                self.issue_command(self.nexttoexecute)
            elif requestedcommand not in self.executed:
                self.logger.write("State", "executing command %d." % self.nexttoexecute)
                # check to see if there was a meta command precisely WINDOW commands ago that should now take effect
                # We are calling performcore 2 times, the timing gets screwed plus this is very unefficient
                if self.nexttoexecute > WINDOW:
                    self.logger.write("State", "performcore %d" % (self.nexttoexecute-WINDOW))
                    self.performcore(msg, self.nexttoexecute-WINDOW, True, designated=designated)
                self.logger.write("State", "performcore %d" % self.nexttoexecute)
                self.performcore(msg, self.nexttoexecute, designated=designated)
                self.nexttoexecute += 1
                # the window just got bumped by one
                # check if there are pending commands, and issue one of them
                self.issue_command(self.nexttoexecute)
        self.logger.write("State", "Returning from PERFORM!")
            
    def initiate_command(self, givenproposal):
        # Add command to pending commands
        givencommandnumber = self.find_commandnumber()
        self.add_to_pendingcommands(givencommandnumber, givenproposal)
        # Try issuing command
        self.issue_command(givencommandnumber)

    def issue_command(self, candidatecommandno):
        """propose a command from the pending commands"""
        self.logger.write("State:", "issuing pending command")
        if self.pendingcommands.has_key(candidatecommandno):
            if self.active:
                self.do_command_propose_from_pending(candidatecommandno)
            else:
                self.do_command_prepare_from_pending(candidatecommandno)

    def msg_perform(self, conn, msg):
        """received a PERFORM message, perform it and send an UPDATE message to the source if necessary"""
        self.perform(msg)

        if not self.stateuptodate and (self.type == NODE_REPLICA or self.type == NODE_NAMESERVER):
            self.logger.write("State", "Updating..")
            if msg.commandnumber == 1:
                self.stateuptodate = True
                return
            updatemessage = UpdateMessage(MSG_UPDATE, self.me)
            self.send(updatemessage, peer=msg.source)

    def msg_helo(self, conn, msg):
        self.logger.write("State", "Received HELO from %s" % (msg.source))
        # This is the first acceptor, it has to be added by this replica
        if msg.source.type == NODE_ACCEPTOR and len(self.groups[NODE_ACCEPTOR]) == 0:
            self.logger.write("State", "Adding the first acceptor")
            self.groups[msg.source.type].add(msg.source)
            # Agree on adding the first replica and this first acceptor
            # Add the Acceptor
            addcommand = self.create_add_command(msg.source)
            self.update_leader()
            self.initiate_command(addcommand)
            for i in range(WINDOW):
                noopcommand = self.create_noop_command()
                self.initiate_command(noopcommand)
            # Add self
            addcommand = self.create_add_command(self.me)
            self.update_leader()
            self.initiate_command(addcommand)
            for i in range(WINDOW):
                noopcommand = self.create_noop_command()
                self.initiate_command(noopcommand)
        else:
            self.update_leader()
            if self.isleader:
                self.logger.write("State", "Adding the new node")
                addcommand = self.create_add_command(msg.source)
                self.update_leader()
                self.initiate_command(addcommand)
                self.logger.write("State", "Add command created: %s" % str(addcommand))
                for i in range(WINDOW+3):
                    noopcommand = self.create_noop_command()
                    self.initiate_command(noopcommand)
            else:
                self.logger.write("State", "Not the leader, sending a HELOREPLY")
                self.logger.write("State", "Leader is %s" % self.find_leader())
                heloreplymessage = HandshakeMessage(MSG_HELOREPLY, self.me, self.find_leader())
                self.send(heloreplymessage, peer=msg.source)
            
    def msg_update(self, conn, msg):
        """a replica needs to be updated on the set of past decisions, send caller's decisions"""
        updatereplymessage = UpdateMessage(MSG_UPDATEREPLY, self.me, self.decisions)
        self.send(updatereplymessage, peer=msg.source)

    def msg_updatereply(self, conn, msg):
        """merge decisions received with local decisions"""
        for key,value in self.decisions.iteritems():
            if msg.decisions.has_key(key):
                assert self.decisions[key] == msg.decisions[key], "Update Error"
        # update decisions cumulatively
        self.decisions.update(msg.decisions)
        self.decisionset = set(self.decisions.values())
        self.usedcommandnumbers = self.usedcommandnumbers.union(set(self.decisions.keys()))
        # Execute the ones that we can execute
        while self.decisions.has_key(self.nexttoexecute):
            requestedcommand = self.decisions[self.nexttoexecute]
            if requestedcommand in self.executed:
                self.logger.write("State", "Previously executed command %d." % self.nexttoexecute)
                self.nexttoexecute += 1
            elif requestedcommand not in self.executed:
                self.logger.write("State", "executing command %d." % self.nexttoexecute)
                # check to see if there was a meta command precisely WINDOW commands ago that should now take effect
                # We are calling performcore 2 times, the timing gets screwed plus this is very unefficient
                if self.nexttoexecute > WINDOW:
                    self.logger.write("State", "performcore %d" % (self.nexttoexecute-WINDOW))
                    self.performcore(msg, self.nexttoexecute-WINDOW, True)
                self.logger.write("State", "performcore %d" % self.nexttoexecute)
                self.performcore(msg, self.nexttoexecute)
                self.nexttoexecute += 1
        # the window got bumped
        # check if there are pending commands, and issue one of them
        self.issue_command(self.nexttoexecute)
        self.logger.write("State", "Update is done!")
        self.stateuptodate = True

    def do_noop(self):
        self.logger.write("State:", "doing noop!")

    def _add_node(self, nodetype, nodename):
        nodetype = int(nodetype)
        self.logger.write("State", "Adding node: %s %s" % (node_names[nodetype], nodename))
        ipaddr,port = nodename.split(":")
        nodepeer = Peer(ipaddr,int(port),nodetype)
        self.groups[nodetype].add(nodepeer)
        
    def _del_node(self, nodetype, nodename):
        nodetype = int(nodetype)
        self.logger.write("State", "Deleting node: %s %s" % (node_names[nodetype], nodename))
        ipaddr,port = nodename.split(":")
        nodepeer = Peer(ipaddr,int(port),nodetype)
        self.groups[nodetype].remove(nodepeer)

    def _garbage_collect(self, garbagecommandnumber):
        """ garbage collect """
        self.logger.write("State", "Initiating garbage collection upto cmd#%d" % garbagecommandnumber)
        garbagemsg = GarbageCollectMessage(MSG_GARBAGECOLLECT,self.me,commandnumber=garbagecommandnumber,snapshot=self.object)
        self.send(garbagemsg,group=self.groups[NODE_ACCEPTOR])
            
# LEADER STATE
    def become_leader(self):
        """Leader State
        - active: indicates if the Leader has a *good* ballotnumber
        - ballotnumber: the highest ballotnumber Leader has used
        - outstandingprepares: ResponseCollector dictionary for MSG_PREPARE,
        indexed by ballotnumber
        - outstandingproposes: ResponseCollector dictionary for MSG_PROPOSE,
        indexed by commandnumber
        - receivedclientrequests: commands received from clients as
        <(client,clientcommandnumber):command> mappings
        - clientpool: connections to clients
        - backoff: backoff amount that is used to determine how much a leader should
        backoff during a collusion
        - commandgap: next commandnumber that will be used by this leader
        """
        if not self.isleader:
            self.isleader = True
            self.active = False
            self.ballotnumber = (0,self.id)
            self.outstandingprepares = {}
            self.outstandingproposes = {}
            self.receivedclientrequests = {}
            self.backoff = 0
            self.commandgap = 1
            
            backoff_thread = Thread(target=self.update_backoff)
            backoff_event.clear()
            backoff_thread.start()
            self.logger.write("State", "Becoming LEADER!")
            
    def unbecome_leader(self):
        """drop LEADER state, become a replica"""
        # fail-stop tolerance, coupled with retries in the client, mean that a 
        # leader can at any time discard all of its internal state and the protocol
        # will still work correctly.
        self.logger.write("State:", "Unbecoming LEADER!")
        self.type = NODE_REPLICA
        self.isleader = False
        backoff_event.set()

    def update_backoff(self):
        """used by the backoffthread to decrease the backoff amount by half periodically"""
        while not backoff_event.isSet():
            self.backoff = self.backoff/2
            backoff_event.wait(BACKOFFDECREASETIMEOUT)

    def detect_colliding_leader(self,ballotnumber):
        """detects a colliding leader from the highest ballotnumber received from acceptors"""
        otherleader_addr,otherleader_port = ballotnumber[BALLOTNODE].split(":")
        otherleader = Peer(otherleader_addr, int(otherleader_port), NODE_REPLICA)
        return otherleader
            
    def find_leader(self):
        """returns the minimum peer as the leader"""
        if len(self.groups[NODE_REPLICA].members) > 0:
            return self.groups[NODE_REPLICA].members[0]
        return self.me
        
    def update_leader(self):
        """checks which node is the leader and changes the state of the caller if necessary"""
        chosenleader = self.find_leader()
        self.logger.write("State", "Chosen LEADER: %s" % str(chosenleader))
        if self.me == chosenleader:
            # caller needs to become a leader
            if not self.isleader:
                # check to see if caller has full history
                if not self.stateuptodate:
                    self.leader_initializing = True
                self.become_leader()
        elif self.isleader:
            # there is some other replica that should act as a leader
            self.unbecome_leader()

    def update_ballotnumber(self,seedballotnumber):
        """update the ballotnumber with a higher value than the given ballotnumber"""
        temp = (seedballotnumber[BALLOTNO]+1,self.ballotnumber[BALLOTNODE])
        self.logger.write("State:", "Updated ballotnumber to %s" % str(temp))
        self.ballotnumber = temp

    def find_commandnumber(self):
        """returns the first gap in proposals and decisions combined"""
        while self.commandgap <= len(self.usedcommandnumbers):
            if self.commandgap in self.usedcommandnumbers:
                self.commandgap += 1
            else:
                self.logger.write("State", "Picked command number: %d" % self.commandgap)
                self.usedcommandnumbers.add(self.commandgap)
                return self.commandgap
        self.logger.write("State", "Picked command number: %d" % self.commandgap)
        self.usedcommandnumbers.add(self.commandgap)
        return self.commandgap

    def add_to_executed(self, key, value):
        self.executed[key] = value

    def add_to_decisions(self, key, value):
        self.decisions[key] = value
        self.decisionset.add(value)
        self.usedcommandnumbers.add(key)

    def add_to_proposals(self, key, value):
        self.proposals[key] = value
        self.proposalset.add(value)
        self.usedcommandnumbers.add(key)

    def add_to_pendingcommands(self, key, value):
        self.pendingcommands[key] = value
        self.pendingcommandset.add(value)

    def remove_from_executed(self, key):
        del self.executed[key]

    def remove_from_decisions(self, key):
        self.decisionset.remove(self.decisions[key])
        del self.decisions[key]
        self.usedcommandnumbers.remove(key)
        self.commandgap = key

    def remove_from_proposals(self, key):
        self.proposalset.remove(self.proposals[key])
        del self.proposals[key]
        self.usedcommandnumbers.remove(key)
        self.commandgap = key

    def remove_from_pendingcommands(self, key):
        self.pendingcommandset.remove(self.pendingcommands[key])
        del self.pendingcommands[key]

    def handle_client_command(self, givencommand, prepare=False):
        """handle received command
        - if it has been received before check if it has been executed
        -- if it has been executed send the result
        -- if it has not been executed yet send INPROGRESS
        - if this request has not been received before initiate a Paxos round for the command"""
        if not self.isleader:
            self.logger.write("Error", "Shouldn't have come here: Called to handle client command but not Leader.")
            clientreply = ClientReplyMessage(MSG_CLIENTREPLY, self.me,
                                             replycode=CR_REJECTED,
                                             inresponseto=givencommand.clientcommandnumber)
            self.logger.write("State", "Rejecting clientrequest: %s" % str(clientreply))
            conn = self.clientpool.get_connection_by_peer(givencommand.client)
            if conn is not None:
                conn.send(clientreply)
            else:
                self.logger.write("Error", "Can't create connection to client: %s - Result not sent." % str(givencommand.client))
            return
        
        if self.receivedclientrequests.has_key((givencommand.client, givencommand.clientcommandnumber)):
            self.logger.write("State", "Client request received previously:")
            self.logger.write("State", "Client: %s Commandnumber: %s\nAcceptors: %s"
                              % (str(givencommand.client),
                                 str(givencommand.clientcommandnumber),
                                 str(self.groups[NODE_ACCEPTOR])))
            # Check if the request has been executed
            if self.executed.has_key(givencommand):
                # send REPLY
                print self.executed[givencommand]
                print self.executed[givencommand][RESULT]
                clientreply = ClientReplyMessage(MSG_CLIENTREPLY, self.me,
                                                 reply=self.executed[givencommand][RESULT],
                                                 replycode=self.executed[givencommand][RCODE],
                                                 inresponseto=givencommand.clientcommandnumber)
                self.logger.write("State", "Clientreply: %s" % str(clientreply))
            # Check if the request is somewhere in the Paxos pipeline: pendingcommands, proposals, decisions
            elif givencommand in self.pendingcommandset or givencommand in self.proposalset or givencommand in self.decisionset:
                # send INPROGRESS
                clientreply = ClientReplyMessage(MSG_CLIENTREPLY, self.me,
                                                 replycode=CR_INPROGRESS,
                                                 inresponseto=givencommand.clientcommandnumber)
                self.logger.write("State", "Clientreply: %s\nAcceptors: %s"
                                  % (str(clientreply),str(self.groups[NODE_ACCEPTOR])))
            conn = self.clientpool.get_connection_by_peer(givencommand.client)
            if conn is not None:
                conn.send(clientreply)
            else:
                self.logger.write("Error", "Can't create connection to client: %s - Reply not sent." % str(givencommand.client))
        else:
            # The caller haven't received this command before
            self.receivedclientrequests[(givencommand.client,givencommand.clientcommandnumber)] = givencommand
            self.logger.write("State", "Initiating a new command. Leader is active: %s" % self.active)
            self.initiate_command(givencommand)

    def msg_clientrequest(self, conn, msg):
        """called holding self.lock
        handles clientrequest message received according to replica's state
        - if not leader: reject
        - if leader: add connection to client connections and handle request"""
        try:
            if self.token and msg.token != self.token:
                self.logger.write("Error", "Security Token mismatch.")
                clientreply = ClientReplyMessage(MSG_CLIENTREPLY,
                                                 self.me,
                                                 replycode=CR_REJECTED,
                                                 inresponseto=msg.command.clientcommandnumber)
                conn.send(clientreply)
        except AttributeError:
            pass
        if self.type == NODE_NAMESERVER:
            self.logger.write("Error", "NAMESERVER got a CLIENTREQUEST")
            return
        # Check to see if Leader
        self.update_leader()
        if not self.isleader:
            # Check the Leader to see if the Client had a reason to think that we are the leader
            if self.leader_is_alive():
                self.logger.write("State", "Not Leader: Rejecting CLIENTREQUEST")
                clientreply = ClientReplyMessage(MSG_CLIENTREPLY,
                                                 self.me,
                                                 replycode=CR_REJECTED,
                                                 inresponseto=msg.command.clientcommandnumber)
                self.logger.write("State", "Clientreply: %s\nAcceptors: %s"
                                  % (str(clientreply), str(self.groups[NODE_ACCEPTOR])))
                conn.send(clientreply)
                return
            self.update_leader()
        # Leader should accept a request even if it's not ready as this
        # way it will make itself ready during the prepare stage.
        if self.isleader:
            self.clientpool.add_connection_to_peer(msg.source, conn)
            if self.leader_initializing:
                self.handle_client_command(msg.command, prepare=True)
            else:
                self.handle_client_command(msg.command)

    def msg_incclientrequest(self, conn, msg):
        """handles inconsistent requests from the client"""
        commandtuple = tuple(msg.command.command)
        commandname = commandtuple[0]
        commandargs = commandtuple[1:]
        send_result_to_client = True
        try:
            method = getattr(self.object, commandname)
            try:
                givenresult = self._apply_args_to_method(method, commandargs, command)
                clientreplycode = CR_OK
                send_result_to_client = True
            except BlockingReturn as blockingretexp:
                givenresult = blockingretexp.returnvalue
                clientreplycode = CR_BLOCK
                send_result_to_client = True
            except UnblockingReturn as unblockingretexp:
                # Get the information about the method call
                # These will be used to update executed and
                # to send reply message to the caller client
                givenresult = unblockingretexp.returnvalue
                unblocked = unblockingretexp.unblocked
                clientreplycode = CR_OK
                send_result_to_client = True
                # If there are clients to be unblocked that have
                # been blocked previously send them unblock messages
                for unblockedclientcommand in unblocked.iterkeys():
                    self.send_reply_to_client(CR_UNBLOCK, None, unblockedclientcommand)
            except Exception as e:
                givenresult = e
                clientreplycode = CR_EXCEPTION
                send_result_to_client = True
                unblocked = {}
        except (TypeError, AttributeError) as t:
            self.logger.write("Execution Error", "command not supported: %s" % (command))
            self.logger.write("Execution Error", "%s" % str(t))
            givenresult = 'COMMAND NOT SUPPORTED'
            clientreplycode = CR_EXCEPTION
            unblocked = {}
            send_result_to_client = True
        if commandname not in METACOMMANDS and send_result_to_client:
            self.send_reply_to_client(clientreplycode, givenresult, command)
            
    def msg_clientreply(self, conn, msg):
        """this only occurs in response to commands initiated by the shell"""
        print "Commandline Debugging:", msg
        
## PAXOS METHODS
    def do_command_propose_from_pending(self, givencommandnumber):
        """Initiates givencommandnumber from pendingcommands list.
        Stage p2a.
        - Remove command from pending and transfer it to proposals
        - If no Acceptors, retreat and return
        - Else start from the PROPOSE STAGE:
        -- create MSG_PROPOSE: message carries ballotnumber, commandnumber, proposal
        -- create ResponseCollector object for PROPOSE STAGE:
        ResponseCollector keeps the state related to MSG_PROPOSE
        -- add the ResponseCollector to the outstanding propose set
        -- send MSG_PROPOSE to Acceptor nodes
        """
        givenproposal = self.pendingcommands[givencommandnumber]
        self.remove_from_pendingcommands(givencommandnumber)
        self.add_to_proposals(givencommandnumber, givenproposal)
        recentballotnumber = self.ballotnumber
        self.logger.write("State", "Proposing command: %d:%s with ballotnumber %s"
                          % (givencommandnumber,givenproposal,str(recentballotnumber)))
        # Since we never propose a commandnumber that is beyond the window,
        # we can simply use the current acceptor set here
        prc = ResponseCollector(self.groups[NODE_ACCEPTOR], recentballotnumber,
                                givencommandnumber, givenproposal)
        if len(prc.acceptors) == 0:
            self.logger.write("Error", "There are no Acceptors, returning!")
            self.remove_from_proposals(givencommandnumber)
            self.add_to_pendingcommands(givencommandnumber, givenproposal)
            return
        self.outstandingproposes[givencommandnumber] = prc
        propose = PaxosMessage(MSG_PROPOSE, self.me, recentballotnumber,
                               commandnumber=givencommandnumber,
                               proposal=givenproposal)
        # the msgs sent may be less than the number of prc.acceptors
        # if a connection to an acceptor is lost
        msgids = self.send(propose, group=prc.acceptors)
        # add sent messages to the sent proposes
        prc.sent.extend(msgids)
                    
    def do_command_prepare_from_pending(self, givencommandnumber):
        """Initiates givencommandnumber from pendingcommands list.
        Stage p1a.
        - Remove command from pending and transfer it to proposals
        - If no Acceptors, retreat and return
        - Else start from the PREPARE STAGE:
        -- create MSG_PREPARE: message carries the corresponding ballotnumber
        -- create ResponseCollector object for PREPARE STAGE:
        ResponseCollector keeps the state related to MSG_PREPARE
        -- add the ResponseCollector to the outstanding prepare set
        -- send MSG_PREPARE to Acceptor nodes
        """
        givenproposal = self.pendingcommands[givencommandnumber]
        self.remove_from_pendingcommands(givencommandnumber)
        self.add_to_proposals(givencommandnumber, givenproposal)
        newballotnumber = self.ballotnumber
        self.logger.write("State", "Preparing command: %d:%s with ballotnumber %s"
                          % (givencommandnumber, givenproposal,str(newballotnumber)))
        prc = ResponseCollector(self.groups[NODE_ACCEPTOR], newballotnumber,
                                givencommandnumber, givenproposal)
        if len(prc.acceptors) == 0:
            self.logger.write("Error", "There are no Acceptors, returning!")
            self.remove_from_proposals(givencommandnumber)
            self.add_to_pendingcommands(givencommandnumber, givenproposal)
            return
        self.outstandingprepares[newballotnumber] = prc
        prepare = PaxosMessage(MSG_PREPARE, self.me, newballotnumber)
        msgids = self.send(prepare, group=prc.acceptors)
        # the msgs sent may be less than the number of prc.acceptors if a connection to an acceptor is lost
        # add sent messages to sent prepares
        prc.sent.extend(msgids)

## PAXOS MESSAGE HANDLERS
    def msg_prepare_adopted(self, conn, msg):
        """MSG_PREPARE_ADOPTED is handled only if it belongs to an outstanding MSG_PREPARE,
        otherwise it is discarded.
        When MSG_PREPARE_ADOPTED is received, the corresponding ResponseCollector is retrieved
        and its state is updated accordingly.

        State Updates:
        - message is added to the received dictionary
        - the pvalue with the ResponseCollector's commandnumber is added to the possiblepvalueset
        - if naccepts is greater than the quorum size PREPARE STAGE is successful.
        -- Start the PROPOSE STAGE:
        --- create the pvalueset with highest ballotnumbers for distinctive commandnumbers
        --- update own proposals dictionary according to pmax dictionary
        --- remove the old ResponseCollector from the outstanding prepare set
        --- run the PROPOSE STAGE for each pvalue in proposals dictionary
        ---- create ResponseCollector object for PROPOSE STAGE: ResponseCollector keeps
        the state related to MSG_PROPOSE
        ---- add the new ResponseCollector to the outstanding propose set
        ---- create MSG_PROPOSE: message carries the corresponding ballotnumber, commandnumber and the proposal
        ---- send MSG_PROPOSE to the same Acceptor nodes from the PREPARE STAGE
        """
        if self.outstandingprepares.has_key(msg.inresponseto):
            prc = self.outstandingprepares[msg.inresponseto]
            prc.received[msg.source] = msg
            self.logger.write("Paxos State", "got an accept for ballotno %s commandno %s proposal %s with %d out of %d" % (prc.ballotnumber, prc.commandnumber, prc.proposal, len(prc.received), prc.ntotal))
            assert msg.ballotnumber == prc.ballotnumber, "[%s] MSG_PREPARE_ADOPTED can't have non-matching ballotnumber" % self
            # add all the p-values from the response to the possiblepvalueset
            if msg.pvalueset is not None:
                prc.possiblepvalueset.union(msg.pvalueset)

            if len(prc.received) >= prc.nquorum:
                self.logger.write("Paxos State", "suffiently many accepts on prepare!")
                # take this response collector out of the outstanding prepare set
                del self.outstandingprepares[msg.inresponseto]
                # choose pvalues with distinctive commandnumbers and highest ballotnumbers
                pmaxset = prc.possiblepvalueset.pmax()
                for commandnumber,proposal in pmaxset.iteritems():
                    self.add_to_proposals(commandnumber, proposal)
                # If the commandnumber we were planning to use is overwritten
                # we should try proposing with a new commandnumber
                if self.proposals[prc.commandnumber] != prc.proposal:
                    self.initiate_command(prc.proposal)
                for chosencommandnumber,chosenproposal in self.proposals.iteritems():
                    self.logger.write("Paxos State", "Sending PROPOSE for %d, %s" % (chosencommandnumber, chosenproposal))
                    newprc = ResponseCollector(prc.acceptors, prc.ballotnumber, chosencommandnumber, chosenproposal)
                    self.outstandingproposes[chosencommandnumber] = newprc
                    propose = PaxosMessage(MSG_PROPOSE,self.me,prc.ballotnumber,commandnumber=chosencommandnumber,proposal=chosenproposal)
                    self.send(propose, group=newprc.acceptors)
                # As leader collected all proposals from acceptors its state is up-to-date and it is done initializing
                self.leader_initializing = False
                self.stateuptodate = True
                # become active
                self.active = True

    def msg_prepare_preempted(self, conn, msg):
        """MSG_PREPARE_PREEMPTED is handled only if it belongs to an outstanding MSG_PREPARE,
        otherwise it is discarded.
        A MSG_PREPARE_PREEMPTED causes the PREPARE STAGE to be unsuccessful, hence the current
        state is deleted and a ne PREPARE STAGE is initialized.

        State Updates:
        - kill the PREPARE STAGE that received a MSG_PREPARE_PREEMPTED
        -- remove the old ResponseCollector from the outstanding prepare set
        - remove the command from proposals, add it to pendingcommands
        - update the ballotnumber
        - initiate command
        """
        if self.outstandingprepares.has_key(msg.inresponseto):
            prc = self.outstandingprepares[msg.inresponseto]
            self.logger.write("Paxos State", "got a reject for ballotno %s commandno %s proposal %s with %d out of %d" % (prc.ballotnumber, prc.commandnumber, prc.proposal, len(prc.received), prc.ntotal))
            # take this response collector out of the outstanding prepare set
            del self.outstandingprepares[msg.inresponseto]
            # become inactive
            self.active = False
            # update the ballot number
            self.update_ballotnumber(msg.ballotnumber)
            self.remove_from_proposals(prc.commandnumber)
            self.add_to_pendingcommands(prc.commandnumber, prc.proposal)
            # backoff -- we're holding the node lock, so no other state machine code can make progress
            leader_causing_reject = self.detect_colliding_leader(msg.ballotnumber)
            if leader_causing_reject < self.me:
                # if caller lost to a replica whose name precedes its, back off more
                self.backoff += BACKOFFINCREASE
            time.sleep(self.backoff)
            self.initiate_command(prc.proposal)

    def msg_propose_accept(self, conn, msg):
        """MSG_PROPOSE_ACCEPT is handled only if it belongs to an outstanding MSG_PREPARE,
        otherwise it is discarded.
        When MSG_PROPOSE_ACCEPT is received, the corresponding ResponseCollector is retrieved
        and its state is updated accordingly.

        State Updates:
        - message is added to the received dictionary
        - if length of received is greater than the quorum size, PROPOSE STAGE is successful.
        -- remove the old ResponseCollector from the outstanding prepare set
        -- create MSG_PERFORM: message carries the chosen commandnumber and proposal.
        -- send MSG_PERFORM to all Replicas and Leaders
        -- execute the command
        """
        self.logger.write("State", "entered propose accept")
        if self.outstandingproposes.has_key(msg.commandnumber):
            prc = self.outstandingproposes[msg.commandnumber]
            if msg.inresponseto == prc.ballotnumber:
                prc.received[msg.source] = msg
                self.logger.write("Paxos State",
                                  "got an accept for proposal ballotno %s commandno %s proposal %s making %d out of %d accepts"
                                  % (prc.ballotnumber, prc.commandnumber, prc.proposal, len(prc.received), prc.ntotal))
                if len(prc.received) >= prc.nquorum:
                    self.logger.write("Paxos State", "Agreed on %s" % prc.proposal) 
                    # take this response collector out of the outstanding propose set
                    self.add_to_proposals(prc.commandnumber, prc.proposal)
                    # delete outstanding messages that caller doesn't need to check for anymore
                    del self.outstandingproposes[msg.commandnumber]
                    # now we can perform this action on the replicas
                    performmessage = PaxosMessage(MSG_PERFORM, self.me,
                                                  commandnumber=prc.commandnumber,
                                                  proposal=prc.proposal)
                    try:
                        self.logger.write("Paxos State", "Sending PERFORM!")
                        if len(self.groups[NODE_REPLICA]) > 0:
                            self.send(performmessage, group=self.groups[NODE_REPLICA])
                        if len(self.groups[NODE_NAMESERVER]) > 0:
                            self.send(performmessage, group=self.groups[NODE_NAMESERVER])
                    except:
                        self.logger.write("Connection Error", "Couldn't send perform messages!")
                    self.perform(performmessage, designated=True)
            self.logger.write("State", "returning from msg_propose_accept")
        
    def msg_propose_reject(self, conn, msg):
        """MSG_PROPOSE_REJECT is handled only if it belongs to an outstanding MSG_PROPOSE,
        otherwise it is discarded.
        A MSG_PROPOSE_REJECT causes the PROPOSE STAGE to be unsuccessful, hence the current
        state is deleted and a new PREPARE STAGE is initialized.

        State Updates:
        - kill the PROPOSE STAGE that received a MSG_PROPOSE_REJECT
        -- remove the old ResponseCollector from the outstanding prepare set
        - remove the command from proposals, add it to pendingcommands
        - update the ballotnumber
        - initiate command
        """
        if self.outstandingproposes.has_key(msg.commandnumber):
            prc = self.outstandingproposes[msg.commandnumber]
            if msg.inresponseto == prc.ballotnumber:
                self.logger.write("Paxos State", "got a reject for proposal ballotno %s commandno %s proposal %s still %d out of %d accepts" % \
                       (prc.ballotnumber, prc.commandnumber, prc.proposal, len(prc.received), prc.ntotal))
                # take this response collector out of the outstanding propose set
                del self.outstandingproposes[msg.commandnumber]
                # become inactive
                self.active = False
                # update the ballot number
                self.update_ballotnumber(msg.ballotnumber)
                # remove the proposal from proposal
                self.remove_from_proposals(prc.commandnumber)
                self.add_to_pendingcommands(prc.commandnumber, prc.proposal)
                leader_causing_reject = self.detect_colliding_leader(msg.ballotnumber)
                if leader_causing_reject < self.me:
                    # if caller lost to a replica whose name precedes its, back off more
                    self.backoff += BACKOFFINCREASE
                self.logger.write("Paxos State", "There is another leader, backing off.")
                time.sleep(self.backoff)
                self.initiate_command(prc.proposal)

    def ping_leader(self):
        """used to ping the current leader periodically"""
        while True:
            currentleader = self.find_leader()
            if currentleader != self.me:
                self.logger.write("State", "Sending PING to %s" % currentleader)
                pingmessage = HandshakeMessage(MSG_PING, self.me)
                success = self.send(pingmessage, peer=currentleader)
                if success < 0:
                    self.logger.write("State", "Leader not responding, removing current leader from the replicalist")
                    self.groups[NODE_REPLICA].remove(currentleader)
            time.sleep(LIVENESSTIMEOUT)

    def leader_is_alive(self):
        currentleader = self.find_leader()
        if currentleader != self.me:
            self.logger.write("State", "Sending PING to %s" % currentleader)
            pingmessage = HandshakeMessage(MSG_PING, self.me)
            success = self.send(pingmessage, peer=currentleader)
            if success < 0:
                self.logger.write("State", "Leader not reachable, removing current leader from the replicalist")
                self.groups[NODE_REPLICA].remove(currentleader)
                return False
        return True

    def create_delete_command(self, node):
        mynumber = self.metacommandnumber
        self.metacommandnumber += 1
        nodename = node.addr + ":" + str(node.port)
        operationtuple = ("_del_node", node.type, nodename)
        command = Command(self.me, mynumber, operationtuple)
        return command

    def create_add_command(self, node):
        mynumber = self.metacommandnumber
        self.metacommandnumber += 1
        nodename = node.addr + ":" + str(node.port)
        operationtuple = ("_add_node", node.type, nodename)
        command = Command(self.me, mynumber, operationtuple)
        return command

    def create_noop_command(self):
        mynumber = self.metacommandnumber
        self.metacommandnumber += 1
        nooptuple = ("noop")
        command = Command(self.me, mynumber, nooptuple)
        return command

## SHELL COMMANDS
    def cmd_command(self, *args):
        """shell command [command]: initiate a new command."""
        try:
            cmdproposal = Command(self.me, random.randint(1,10000000), args[1:])
            self.handle_client_command(cmdproposal)
        except IndexError:
            print "command expects only one command"

    def cmd_goleader(self, args):
        """start Leader state""" 
        self.become_leader()

    def cmd_clients(self,args):
        """prints client connections"""
        print self.clientpool

    def cmd_showobject(self, args):
        """print replicated object information""" 
        print self.object

    def cmd_info(self, args):
        """print next commandnumber to execute and executed commands"""
        print "Waiting to execute #%d" % self.nexttoexecute
        print "Decisions:\n"
        for (commandnumber,command) in self.decisions.iteritems():
            temp = "%d:\t%s" %  (commandnumber, command)
            if command in self.executed:
                temp += "\t%s\n" % (str(self.executed[command]))
            print temp

    def cmd_proposals(self,args):
        """prints proposals"""
        for cmdnum,command in self.proposals.iteritems():
            print "%d: %s" % (cmdnum,str(command))

    def cmd_pending(self,args):
        """prints pending commands"""
        for cmdnum,command in self.pendingcommands.iteritems():
            print "%d: %s" % (cmdnum,str(command))

## MESUREMENT OUTPUT
    def msg_output(self, conn, msg):
        time.sleep(10)
        sys.stdout.flush()
        self.send(msg, self.groups[NODE_ACCEPTOR].members[0])
        dumptimers(str(len(self.groups[NODE_REPLICA])+1), str(len(self.groups[NODE_ACCEPTOR])), self.type)
        numclients = len(self.clientpool.poolbypeer.keys())
        dumptimers(str(numclients), str(len(self.groups[NODE_ACCEPTOR])), self.type)
        
## TERMINATION METHODS
    def terminate_handler(self, signal, frame):
        self._graceexit()

    def _graceexit(self, exitcode=0):
        sys.stdout.flush()
        sys.stderr.flush()
        try:
            self.logger.close()
        except:
            pass
        os._exit(exitcode)

def main():
    replicanode = Replica()
    replicanode.startservice()
    signal.signal(signal.SIGINT, replicanode.terminate_handler)
    signal.signal(signal.SIGTERM, replicanode.terminate_handler)
    signal.pause()
    
if __name__=='__main__':
    main()
