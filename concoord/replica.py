'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: The Replica keeps an object and responds to Perform messages received from the Leader.
@copyright: See LICENSE
'''
import inspect
import time
import os, sys
import signal
import cPickle as pickle
from threading import Thread, Lock, Timer, Event
from concoord.pack import Proposal, PValue
from concoord.pvalue import PValueSet
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
            import importlib
            objectloc,a,classname = self.objectname.rpartition('.')
            self.object = None
            try:
                module = importlib.import_module(objectloc)
                if hasattr(module, classname):
                    self.object = getattr(module, classname)()
            except (ValueError, ImportError, AttributeError):
                self.object = None

            if not self.object:
                self.logger.write("Object Error", "Object cannot be found.")
                self._graceexit(1)
            try:
                self.token = getattr(self.object, '_%s__concoord_token' % self.objectname)
            except AttributeError as e:
                if self.debug: self.logger.write("State", "Object initialized without a token.")
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
        # pending metacommands
        self.pendingmetalock = Lock()
        self.pendingmetacommands = set()
        # number for metacommands initiated from this replica
        self.metacommandnumber = 0
        # keep nodes that are recently updated
        self.recentlyupdatedpeerslock = Lock()
        self.recentlyupdatedpeers = []

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
        rstr += "Members:\n%s\n" % "\n".join(str(group) for type,group in self.groups.iteritems())
        rstr += "Waiting to execute command %d.\n" % self.nexttoexecute
        rstr += "Commands:\n"
        for commandnumber, command in self.decisions.iteritems():
            state = ''
            if command in self.executed:
                if isinstance(command, ProposalClientBatch):
                    state = '\t' + str(self.executed[command])
                else:
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

    def _import_object(self, name):
        mod = __import__(name)
        components = name.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod

    def startservice(self):
        """Start the background services associated with a replica."""
        Node.startservice(self)

    @staticmethod
    def _apply_args_to_method(method, args, _concoord_command):
        argspec = inspect.getargspec(method)
        if argspec.args and argspec.args[-1] == '_concoord_command':
            return method(*args, _concoord_command=_concoord_command)
        elif argspec.keywords is not None:
            return method(*args, _concoord_command=_concoord_command)
        else:
            return method(*args)

    def performcore_clientbatch(self, commandbatch, designated=False):
        '''performs all clientrequests in a clientbatch and returns a batched result.'''
        if self.debug: self.logger.write("State", "Performing client batch.")
        clientreplies = []
        for commandtuple in commandbatch.command:
            commandname = commandtuple[0]
            commandargs = commandtuple[1:]
            # Result triple
            clientreplycode, givenresult, unblocked = (-1, None, {})
            try:
                method = getattr(self.object, commandname)
                # Watch out for the lock release and acquire!
                self.lock.release()
                try:
                    givenresult = method(*commandargs)
                    clientreplycode = CR_OK
                except BlockingReturn as blockingretexp:
                    if self.debug: self.logger.write("State", "Blocking Client.")
                    givenresult = blockingretexp.returnvalue
                    clientreplycode = CR_BLOCK
                except UnblockingReturn as unblockingretexp:
                    if self.debug: self.logger.write("State", "Unblocking Client(s).")
                    # Get the information about the method call
                    # These will be used to update executed and
                    # to send reply message to the caller client
                    givenresult = unblockingretexp.returnvalue
                    unblocked = unblockingretexp.unblocked
                    clientreplycode = CR_OK
                    # If there are clients to be unblocked that have
                    # been blocked previously, send them unblock messages
                    for unblockedclientcommand in unblocked.iterkeys():
                        self.send_reply_to_client(CR_UNBLOCK, None, unblockedclientcommand)
                except Exception as e:
                    if self.debug: self.logger.write("Execution Error", "Error during method invocation: %s" % str(e))
                    givenresult = pickle.dumps(e)
                    clientreplycode = CR_EXCEPTION
                    unblocked = {}
                self.lock.acquire()
            except (TypeError, AttributeError) as t:
                if self.debug: self.logger.write("Execution Error",
                                                 "command not supported: %s" % str(commandname))
                if self.debug: self.logger.write("Execution Error", "%s" % str(t))

                givenresult = 'Method Does Not Exist: ', commandname
                clientreplycode = CR_EXCEPTION
                unblocked = {}
            clientreplies.append((clientreplycode, givenresult, unblocked))
        self.add_to_executed(commandbatch, clientreplies)

        if self.isleader and str(commandbatch.client) in self.connectionpool.poolbypeer.keys():
            self.send_replybatch_to_client(clientreplies, commandbatch)

        if self.nexttoexecute % GARBAGEPERIOD == 0 and self.isleader:
            mynumber = self.metacommandnumber
            self.metacommandnumber += 1
            garbagetuple = ("_garbage_collect", self.nexttoexecute)
            garbagecommand = Proposal(self.me, mynumber, garbagetuple)
            if self.leader_initializing:
                self.handle_client_command(garbagecommand, prepare=True)
            else:
                self.handle_client_command(garbagecommand)
        if self.debug: self.logger.write("State:", "returning from performcore!")

    def performcore(self, command, dometaonly=False, designated=False):
        """The core function that performs a given command in a slot number. It
        executes regular commands as well as META-level commands (commands related
        to the managements of the Paxos protocol) with a delay of WINDOW commands."""
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
        if self.debug: self.logger.write("State:", "---> Command: %s DoMetaOnly: %s IsMeta: %s"
                          % (command, dometaonly, ismeta))
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
                if self.debug: self.logger.write("State", "commandname: %s args: %s" % (commandname, str(commandargs)))
                method = getattr(self, commandname)
                clientreplycode = CR_META
                givenresult = self._apply_args_to_method(method, commandargs, command)
                #givenresult = method(*commandargs)
                unblocked = {}
                send_result_to_client = False
            elif not dometaonly and ismeta:
                # meta command, but the window has not passed yet,
                # so just mark it as executed without actually executing it
                # the real execution will take place when the window has expired
                self.add_to_executed(command, (CR_META, META, {}))
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
                    if self.debug: self.logger.write("State", "Blocking Client.")
                    givenresult = blockingretexp.returnvalue
                    clientreplycode = CR_BLOCK
                    send_result_to_client = True
                except UnblockingReturn as unblockingretexp:
                    if self.debug: self.logger.write("State", "Unblocking Client(s).")
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
                    if self.debug: self.logger.write("Execution Error", "Error during method invocation: %s" % str(e))
                    givenresult = pickle.dumps(e)
                    clientreplycode = CR_EXCEPTION
                    send_result_to_client = True
                    unblocked = {}
                self.lock.acquire()
        except (TypeError, AttributeError) as t:
            if self.debug: self.logger.write("Execution Error",
                                             "command not supported: %s" % str(command))
            if self.debug: self.logger.write("Execution Error", "%s" % str(t))

            givenresult = 'Method Does Not Exist: ', commandname
            clientreplycode = CR_EXCEPTION
            unblocked = {}
            send_result_to_client = True
        self.add_to_executed(command, (clientreplycode,givenresult,unblocked))

        if commandname not in METACOMMANDS:
            # if this client contacted me for this operation, return him the response
            if send_result_to_client and self.isleader and str(command.client) in self.connectionpool.poolbypeer.keys():
                self.send_reply_to_client(clientreplycode, givenresult, command)

        if self.nexttoexecute % GARBAGEPERIOD == 0 and self.isleader:
            mynumber = self.metacommandnumber
            self.metacommandnumber += 1
            garbagetuple = ("_garbage_collect", self.nexttoexecute)
            garbagecommand = Proposal(self.me, mynumber, garbagetuple)
            if self.leader_initializing:
                self.handle_client_command(garbagecommand, prepare=True)
            else:
                self.handle_client_command(garbagecommand)
        if self.debug: self.logger.write("State:", "returning from performcore!")

    def send_replybatch_to_client(self, givenresult, command):
        if self.debug: self.logger.write("State", "Sending REPLY to CLIENT")
        clientreply = create_message(MSG_CLIENTREPLY, self.me,
                                     {FLD_REPLY: givenresult,
                                      FLD_REPLYCODE: CR_BATCH,
                                      FLD_INRESPONSETO: command.clientcommandnumber})
        clientconn = self.connectionpool.get_connection_by_peer(command.client)
        if clientconn == None or clientconn.thesocket == None:
            if self.debug: self.logger.write("State", "Client connection does not exist.")
            return
        clientconn.send(clientreply)

    def send_reply_to_client(self, clientreplycode, givenresult, command):
        if self.debug: self.logger.write("State", "Sending REPLY to CLIENT")
        clientreply = create_message(MSG_CLIENTREPLY, self.me,
                                     {FLD_REPLY: givenresult,
                                      FLD_REPLYCODE: clientreplycode,
                                      FLD_INRESPONSETO: command.clientcommandnumber})
        if self.debug: self.logger.write("State", "Clientreply: %s\nAcceptors: %s"
                          % (str(clientreply), str(self.groups[NODE_ACCEPTOR])))
        clientconn = self.connectionpool.get_connection_by_peer(command.client)
        if clientconn == None or clientconn.thesocket == None:
            if self.debug: self.logger.write("State", "Client connection does not exist.")
            return
        clientconn.send(clientreply)

    def perform(self, msg, designated=False):
        """Take a given PERFORM message, add it to the set of decided commands,
        and call performcore to execute."""
        if self.debug: self.logger.write("State:", "Performing msg %s" % str(msg))
        if msg.commandnumber not in self.decisions:
            self.add_to_decisions(msg.commandnumber, msg.proposal)
        # If replica was using this commandnumber for a different proposal, initiate it again
        if msg.commandnumber in self.proposals and msg.proposal != self.proposals[msg.commandnumber]:
            self.pick_commandnumber_add_to_pending(self.proposals[msg.commandnumber])
            self.issue_pending_commands()

        while self.nexttoexecute in self.decisions:
            requestedcommand = self.decisions[self.nexttoexecute]
            if isinstance(requestedcommand, ProposalServerBatch):
                for command in requestedcommand.proposals:
                    self.execute_command(command, msg, designated)
            else:
                self.execute_command(requestedcommand, msg, designated)
            self.nexttoexecute += 1
            # the window just got bumped by one
            # check if there are pending commands, and issue one of them
            self.issue_pending_commands()
        if self.debug: self.logger.write("State", "Returning from PERFORM!")

    def execute_command(self, requestedcommand, msg, designated):
        # commands are executed one by one here.
        if requestedcommand in self.executed:
            if self.debug: self.logger.write("State", "Previously executed command %d."
                                             % self.nexttoexecute)
            # Execute the metacommand associated with this command
            if self.nexttoexecute > WINDOW:
                if self.debug: self.logger.write("State", "performcore %d" % (self.nexttoexecute-WINDOW))
                self.performcore(self.decisions[self.nexttoexecute-WINDOW], True)
            # If we are a leader, we should send a reply to the client for this command
            # in case the client didn't receive the reply from the previous leader
            if self.isleader:
                prevrcode, prevresult, prevunblocked = self.executed[requestedcommand]
                if prevrcode == CR_BLOCK:
                    # As dictionary is not sorted we have to start from the beginning every time
                    for resultset in self.executed.itervalues():
                        if resultset[EXC_UNBLOCKED] == requestedcommand:
                            # This client has been UNBLOCKED
                            prevresult = None
                            prevrcode = CR_UNBLOCK
                # Send a reply to the client only if there was a client
                if type(requestedcommand.command) == str:
                    commandname = requestedcommand.command
                else:
                    commandname = requestedcommand.command[0]
                if (commandname not in METACOMMANDS) and (commandname != 'noop'):
                    if self.debug: self.logger.write("State", "Sending reply to client.")
                    self.send_reply_to_client(prevrcode, prevresult, requestedcommand)
        elif requestedcommand not in self.executed:
            if self.debug: self.logger.write("State", "executing command %s." % str(requestedcommand))
            # check to see if there was a metacommand precisely WINDOW commands ago
            # that should now take effect
            # We are calling performcore 2 times, the timing gets screwed plus this
            # is very unefficient
            if self.nexttoexecute > WINDOW:
                if self.debug: self.logger.write("State", "performcore %d" % (self.nexttoexecute-WINDOW))
                if not (isinstance(self.decisions[self.nexttoexecute-WINDOW], ProposalServerBatch) or
                        isinstance(self.decisions[self.nexttoexecute-WINDOW], ProposalClientBatch)):
                    self.performcore(self.decisions[self.nexttoexecute-WINDOW], True, designated=designated)
            if self.debug: self.logger.write("State", "performcore %s" % str(requestedcommand))
            if isinstance(requestedcommand, ProposalClientBatch):
                self.performcore_clientbatch(requestedcommand, designated=designated)
            else:
                self.performcore(requestedcommand, designated=designated)

    def pick_commandnumber_add_to_pending(self, givenproposal):
        givencommandnumber = self.find_commandnumber()
        self.add_to_pendingcommands(givencommandnumber, givenproposal)

    def issue_next_command(self):
        if self.debug: self.logger.write("State", "Pending commands: %s" % str(self.pendingcommands))
        if self.debug: self.logger.write("State", "Pending commandset: %s" % str(self.pendingcommandset))
        if len(self.pendingcommands) == 0:
            return
        smallestcommandnumber = sorted(self.pendingcommands.keys())[0]
        if smallestcommandnumber in self.pendingcommands:
            if self.active:
                self.do_command_propose_from_pending(smallestcommandnumber)
            else:
                self.do_command_prepare_from_pending(smallestcommandnumber)

    def issue_pending_commands(self):
        if self.debug: self.logger.write("State", "Pending commands: %s" % str(self.pendingcommands))
        if len(self.pendingcommands) == 0:
            return
        sortedcommandnumbers = sorted(self.pendingcommands.keys())
        for smallestcommandnumber in sortedcommandnumbers:
            if self.active:
                self.do_command_propose_from_pending(smallestcommandnumber)
            else:
                self.do_command_prepare_from_pending(smallestcommandnumber)

    def msg_perform(self, conn, msg):
        """received a PERFORM message, perform it and send an
        UPDATE message to the source if necessary"""
        self.perform(msg)

        if not self.stateuptodate and (self.type == NODE_REPLICA or self.type == NODE_NAMESERVER):
            if self.debug: self.logger.write("State", "Updating..")
            if msg.commandnumber == 1:
                self.stateuptodate = True
                return
            updatemessage = create_message(MSG_UPDATE, self.me)
            conn.send(updatemessage)

    def msg_issue(self, conn, msg):
        self.issue_pending_commands()

    def msg_helo(self, conn, msg):
        if self.debug: self.logger.write("State", "Received HELO")
        # This is the first acceptor, it has to be added by this replica
        if msg.source.type == NODE_ACCEPTOR and len(self.groups[NODE_ACCEPTOR]) == 0:
            if self.debug: self.logger.write("State", "Adding the first acceptor")
            self.groups[msg.source.type][msg.source] = 0
            # Agree on adding the first acceptor and self:
            self.become_leader()
            # Add acceptor
            addcommand = self.create_add_command(msg.source)
            self.pick_commandnumber_add_to_pending(addcommand)
            for i in range(WINDOW):
                noopcommand = self.create_noop_command()
                self.pick_commandnumber_add_to_pending(noopcommand)
            self.issue_pending_commands()
            # Add self
            addcommand = self.create_add_command(self.me)
            self.pick_commandnumber_add_to_pending(addcommand)
            for i in range(WINDOW):
                noopcommand = self.create_noop_command()
                self.pick_commandnumber_add_to_pending(noopcommand)
            self.issue_pending_commands()
        elif len(self.groups[NODE_ACCEPTOR]) == 0:
            if self.debug: self.logger.write("State", "There are no acceptors. Cannot add new node.")
            heloreplymessage = create_message(MSG_HELOREPLY, self.me,
                                              {FLD_LEADER: self.find_leader()})
            conn.send(heloreplymessage)
        else:
            if self.isleader:
                if self.debug: self.logger.write("State", "Adding the new node")
                addcommand = self.create_add_command(msg.source)
                self.pick_commandnumber_add_to_pending(addcommand)
                for i in range(WINDOW+3):
                    noopcommand = self.create_noop_command()
                    self.pick_commandnumber_add_to_pending(noopcommand)
                self.issue_pending_commands()
            else:
                if self.debug: self.logger.write("State", "Not the leader, sending a HELOREPLY")
                if self.debug: self.logger.write("State", "Leader is %s" % str(self.find_leader()))
                heloreplymessage = create_message(MSG_HELOREPLY, self.me,
                                                  {FLD_LEADER: self.find_leader()})
                conn.send(heloreplymessage)

    def msg_update(self, conn, msg):
        """a replica needs to be updated on the set of past decisions, send caller's decisions"""
        # This should be done only if it has not been done recently.
        with self.recentlyupdatedpeerslock:
            if msg.source in self.recentlyupdatedpeers:
                return
        updatereplymessage = create_message(MSG_UPDATEREPLY, self.me,
                                            {FLD_DECISIONS: self.decisions})
        conn.send(updatereplymessage)
        with self.recentlyupdatedpeerslock:
            self.recentlyupdatedpeers.append(msg.source)

    def msg_updatereply(self, conn, msg):
        """merge decisions received with local decisions"""
        # If the node is already up-to-date, return.
        if self.stateuptodate:
            return
        for key,value in self.decisions.iteritems():
            if key in msg.decisions:
                assert self.decisions[key] == msg.decisions[key], "Update Error"
        # update decisions cumulatively
        self.decisions.update(msg.decisions)
        self.decisionset = set(self.decisions.values())
        self.usedcommandnumbers = self.usedcommandnumbers.union(set(self.decisions.keys()))
        # Execute the ones that we can execute
        while self.nexttoexecute in self.decisions:
            requestedcommand = self.decisions[self.nexttoexecute]
            if requestedcommand in self.executed:
                if self.debug: self.logger.write("State", "Previously executed command %d." % self.nexttoexecute)
                # Execute the metacommand associated with this command
                if self.nexttoexecute > WINDOW:
                    if self.debug: self.logger.write("State", "performcore %d" % (self.nexttoexecute-WINDOW))
                    self.performcore(self.decisions[self.nexttoexecute-WINDOW], True)
                self.nexttoexecute += 1
            elif requestedcommand not in self.executed:
                if self.debug: self.logger.write("State", "executing command %d." % self.nexttoexecute)

                if self.nexttoexecute > WINDOW:
                    if self.debug: self.logger.write("State", "performcore %d" % (self.nexttoexecute-WINDOW))
                    self.performcore(self.decisions[self.nexttoexecute-WINDOW], True)
                if self.debug: self.logger.write("State", "performcore %d" % self.nexttoexecute)
                self.performcore(self.decisions[self.nexttoexecute])
                self.nexttoexecute += 1
        # the window got bumped
        # check if there are pending commands, and issue one of them
        self.issue_pending_commands()
        if self.debug: self.logger.write("State", "Update is done!")
        self.stateuptodate = True

    def do_noop(self):
        if self.debug: self.logger.write("State:", "doing noop!")

    def _add_node(self, nodetype, nodename):
        nodetype = int(nodetype)
        if self.debug: self.logger.write("State", "Adding node: %s %s" % (node_names[nodetype], nodename))
        ipaddr,port = nodename.split(":")
        nodepeer = Peer(ipaddr,int(port),nodetype)
        self.groups[nodetype][nodepeer] = 0

        # if added node is a replica and this replica is uptodate
        # check leadership state
        if nodetype == NODE_REPLICA and self.stateuptodate:
            chosenleader = self.find_leader()
            if chosenleader == self.me and not self.isleader:
                # become the leader
                if not self.stateuptodate:
                    self.leader_initializing = True
                self.become_leader()
            elif chosenleader != self.me and self.isleader:
                # unbecome the leader
                self.unbecome_leader()

    def _get_ft(self):
        ft_replica = len(self.replicas)-1
        ft_acceptor = int(math.ceil(len(self.acceptors)/2.0))-1
        return "The system can tolerate %d replica and %d acceptor failures." % (ft_replica,ft_acceptor)

    def _del_node(self, nodetype, nodename):
        nodetype = int(nodetype)
        if self.debug: self.logger.write("State", "Deleting node: %s %s" % (node_names[nodetype], nodename))
        ipaddr,port = nodename.split(":")
        nodepeer = Peer(ipaddr,int(port),nodetype)
        try:
            del self.groups[nodetype][nodepeer]
        except KeyError:
            if self.debug: self.logger.write("State",
                                             "Cannot delete node that is not in the view: %s %s"
                                             % (node_names[nodetype], nodename))
        # if deleted node is a replica and this replica is uptodate
        # check leadership state
        if nodetype == NODE_REPLICA and self.uptodate:
            chosenleader = self.find_leader()
            if chosenleader == self.me and not self.isleader:
                # become the leader
                if not self.stateuptodate:
                    self.leader_initializing = True
                self.become_leader()
            elif chosenleader != self.me and self.isleader:
                # unbecome the leader
                self.unbecome_leader()

    def _garbage_collect(self, garbagecommandnumber):
        """ garbage collect """
        if self.debug: self.logger.write("State",
                          "Initiating garbage collection upto cmd#%d"
                          % garbagecommandnumber)
        snapshot = pickle.dumps(self.object)
        garbagemsg = create_message(MSG_GARBAGECOLLECT, self.me,
                                    {FLD_COMMANDNUMBER: garbagecommandnumber,
                                     FLD_SNAPSHOT: snapshot})
        self.send(garbagemsg,group=self.groups[NODE_ACCEPTOR])
        # do local garbage collection
        self.local_garbage_collect(garbagecommandnumber)

    def local_garbage_collect(self, commandnumber):
        """
        Truncates decisions, executed and proposals
        up to given commandnumber
        """
        keys = sorted(self.decisions.keys())
        # Sanity checking
        lastkey = keys[0]
        candelete = True
        for cmdno in keys:
            if cmdno == lastkey:
                lastkey += 1
            else:
                candelete = False
                break
        # Truncating
        if not candelete:
            return False
        for cmdno in keys:
            if cmdno < commandnumber:
                if self.decisions[cmdno] in self.executed:
                    del self.executed[self.decisions[cmdno]]
                    try:
                        del self.proposals[cmdno]
                    except:
                        pass
                    #del self.decisions[cmdno]
                else:
                    break
        return True

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
            self.leader_initializing = True

            backoff_thread = Thread(target=self.update_backoff)
            backoff_event.clear()
            backoff_thread.start()
            if self.debug: self.logger.write("State", "Becoming LEADER!")

    def unbecome_leader(self):
        """drop LEADER state, become a replica"""
        # fail-stop tolerance, coupled with retries in the client, mean that a
        # leader can at any time discard all of its internal state and the protocol
        # will still work correctly.
        if self.debug: self.logger.write("State:", "Unbecoming LEADER!")
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

    def leader_is_alive(self):
        """returns a tuple if the leader is alive and the currentleader"""
        currentleader = self.find_leader()
        if currentleader != self.me:
            if self.debug: self.logger.write("State", "Sending PING to %s" % str(currentleader))
            pingmessage = create_message(MSG_PING, self.me)
            successid = self.send(pingmessage, peer=currentleader)
            if successid < 0:
                self.groups[currentleader.type][currentleader] += 1
                return False, currentleader
        return True, currentleader

    def find_leader(self):
        """returns the minimum peer that is alive as the leader"""
        # sort the replicas first
        replicas = sorted(self.replicas.items(), key=lambda t: t[0])
        if self.debug: self.logger.write("State", "All Replicas in my view:%s" %str(replicas))
        for (replica,liveness) in replicas:
            if liveness == 0:
                del replicas
                if self.debug: self.logger.write("State", "Leader is %s" %str(replica))
                return replica
        del replicas
        if self.debug: self.logger.write("State", "Leader is me")
        return self.me

    def update_ballotnumber(self,seedballotnumber):
        """update the ballotnumber with a higher value than the given ballotnumber"""
        temp = (seedballotnumber[BALLOTNO]+1,self.ballotnumber[BALLOTNODE])
        if self.debug: self.logger.write("State:", "Updated ballotnumber to %s" % str(temp))
        self.ballotnumber = temp

    def find_commandnumber(self):
        """returns the first gap in proposals and decisions combined"""
        while self.commandgap <= len(self.usedcommandnumbers):
            if self.commandgap in self.usedcommandnumbers:
                self.commandgap += 1
            else:
                if self.debug: self.logger.write("State", "Picked command number: %d" % self.commandgap)
                self.usedcommandnumbers.add(self.commandgap)
                return self.commandgap
        if self.debug: self.logger.write("State", "Picked command number: %d" % self.commandgap)
        self.usedcommandnumbers.add(self.commandgap)
        return self.commandgap

    def add_to_executed(self, key, value):
        self.executed[key] = value

    def add_to_decisions(self, key, value):
        self.decisions[key] = value
        if isinstance(value, ProposalServerBatch):
            for item in value.proposals:
                self.decisionset.add(item)
        else:
            self.decisionset.add(value)
        self.usedcommandnumbers.add(key)

    def add_to_proposals(self, key, value):
        self.proposals[key] = value
        if isinstance(value, ProposalServerBatch):
            for item in value.proposals:
                self.proposalset.add(item)
        else:
            self.proposalset.add(value)
        self.usedcommandnumbers.add(key)

    def add_to_pendingcommands(self, key, value):
        # If a Replica adds a pendingcommand before it is up to date
        # it assigns 1 as a commandnumber for a command. This later
        # gets overwritten when the same command is added later with
        # a higher commandnumber in the pendingcommandset but not in
        # in the pendingcommands as they have different keys. The case
        # that causes this to happen should be prevented, adding an if
        # case in this function will not fix the logic, will just get rid
        # of the symptom.
        self.pendingcommands[key] = value
        if isinstance(value, ProposalServerBatch):
            for item in value.proposals:
                self.pendingcommandset.add(item)
        else:
            self.pendingcommandset.add(value)

    def remove_from_executed(self, key):
        del self.executed[key]

    def remove_from_decisions(self, key):
        value = self.decisions[key]
        if isinstance(value, ProposalServerBatch):
            for item in value.proposals:
                self.decisionset.remove(item)
        else:
            self.decisionset.remove(value)
        del self.decisions[key]
        self.usedcommandnumbers.remove(key)
        self.commandgap = key

    def remove_from_proposals(self, key):
        value = self.proposals[key]
        if isinstance(value, ProposalServerBatch):
            for item in value.proposals:
                self.proposalset.remove(item)
        else:
            self.proposalset.remove(value)
        del self.proposals[key]
        self.usedcommandnumbers.remove(key)
        self.commandgap = key

    def remove_from_pendingcommands(self, key):
        value = self.pendingcommands[key]
        if isinstance(value, ProposalServerBatch):
            for item in value.proposals:
                self.pendingcommandset.remove(item)
        else:
            self.pendingcommandset.remove(value)
        del self.pendingcommands[key]

    def handle_client_command(self, givencommand, sendcount=1, prepare=False):
        """handle received command
        - if it has been received before check if it has been executed
        -- if it has been executed send the result
        -- if it has not been executed yet send INPROGRESS
        - if this request has not been received before initiate a Paxos round for the command"""
        if not self.isleader:
            if self.debug: self.logger.write("Error", "Should not have come here: Called to handle client command but not Leader.")
            clientreply = create_message(MSG_CLIENTREPLY, self.me,
                                         {FLD_REPLY: '',
                                          FLD_REPLYCODE: CR_REJECTED,
                                          FLD_INRESPONSETO: givencommand.clientcommandnumber})
            if self.debug: self.logger.write("State", "Rejecting clientrequest: %s" % str(clientreply))
            conn = self.connectionpool.get_connection_by_peer(givencommand.client)
            if conn is not None:
                conn.send(clientreply)
            else:
                if self.debug: self.logger.write("Error", "Cannot create connection to client")
            return

        if sendcount > 0 and (givencommand.client, givencommand.clientcommandnumber) in self.receivedclientrequests:
            if self.debug: self.logger.write("State", "Client request received previously:")
            if self.debug: self.logger.write("State", "Client: %s Commandnumber: %s Acceptors: %s"
                              % (str(givencommand.client),
                                 str(givencommand.clientcommandnumber),
                                 str(self.groups[NODE_ACCEPTOR])))
            # Check if the request has been executed
            if givencommand in self.executed:
                # send REPLY
                clientreply = create_message(MSG_CLIENTREPLY, self.me,
                                             {FLD_REPLY: self.executed[givencommand][EXC_RESULT],
                                              FLD_REPLYCODE: self.executed[givencommand][EXC_RCODE],
                                              FLD_INRESPONSETO: givencommand.clientcommandnumber})
                if self.debug: self.logger.write("State", "Clientreply: %s" % str(clientreply))
            # Check if the request is somewhere in the Paxos pipeline
            elif givencommand in self.pendingcommandset or \
                    givencommand in self.proposalset or \
                    givencommand in self.decisionset:
                # send INPROGRESS
                clientreply = create_message(MSG_CLIENTREPLY, self.me,
                                             {FLD_REPLY: '',
                                              FLD_REPLYCODE: CR_INPROGRESS,
                                              FLD_INRESPONSETO: givencommand.clientcommandnumber})
                if self.debug: self.logger.write("State", "Clientreply: %s\nAcceptors: %s"
                                  % (str(clientreply),str(self.groups[NODE_ACCEPTOR])))
            conn = self.connectionpool.get_connection_by_peer(givencommand.client)
            if conn is not None:
                conn.send(clientreply)
            else:
                if self.debug: self.logger.write("Error", "Cannot create connection to client")
        else:
            # The caller haven't received this command before
            self.receivedclientrequests[(givencommand.client,givencommand.clientcommandnumber)] = givencommand
            if self.debug: self.logger.write("State", "Initiating a new command. Leader is active: %s" % self.active)
            self.pick_commandnumber_add_to_pending(givencommand)
            self.issue_pending_commands()

    def handle_client_command_batch(self, msgconnlist, prepare=False):
        """handle received command
        - if it has been received before check if it has been executed
        -- if it has been executed send the result
        -- if it has not been executed yet send INPROGRESS
        - if this request has not been received before initiate a Paxos round for the command"""
        if not self.isleader:
            if self.debug: self.logger.write("Error",
                              "Should not have come here: Not Leader.")
            for (msg,conn) in msgconnlist:
                clientreply = create_message(MSG_CLIENTREPLY, self.me,
                                             {FLD_REPLY: '',
                                              FLD_REPLYCODE: CR_REJECTED,
                                              FLD_INRESPONSETO: msg.command.clientcommandnumber})
                conn.send(clientreply)
            return

        commandstohandle = []
        for (msg,conn) in msgconnlist:
            if msg.sendcount == 0:
                # The caller haven't received this command before
                self.receivedclientrequests[(msg.command.client,
                                             msg.command.clientcommandnumber)] = msg.command
                commandstohandle.append(msg.command)
                continue
            if (msg.command.client, msg.command.clientcommandnumber) in self.receivedclientrequests:
                if self.debug: self.logger.write("State", "Client request received previously:")
                # Check if the request has been executed
                if msg.command in self.executed:
                    # send REPLY
                    clientreply = create_message(MSG_CLIENTREPLY, self.me,
                                                 {FLD_REPLY: self.executed[msg.command][EXC_RESULT],
                                                  FLD_REPLYCODE: self.executed[msg.command][EXC_RCODE],
                                                  FLD_INRESPONSETO: msg.command.clientcommandnumber})
                    if self.debug: self.logger.write("State", "Clientreply: %s" % str(clientreply))
                # Check if the request is somewhere in the Paxos pipeline
                elif msg.command in self.pendingcommandset or msg.command in self.proposalset \
                        or msg.command in self.decisionset:
                    # send INPROGRESS
                    clientreply = create_message(MSG_CLIENTREPLY, self.me,
                                                 {FLD_REPLY: '',
                                                  FLD_REPLYCODE: CR_INPROGRESS,
                                                  FLD_INRESPONSETO: msg.command.clientcommandnumber})
                    if self.debug: self.logger.write("State", "Clientreply: %s\nAcceptors: %s"
                                      % (str(clientreply),str(self.groups[NODE_ACCEPTOR])))
                conn.send(clientreply)
        if self.debug: self.logger.write("State", "Initiating a new command. Leader is active: %s" % self.active)
        # Check if batching is still required
        if len(commandstohandle) == 0:
            return
        elif len(commandstohandle) == 1:
            self.pick_commandnumber_add_to_pending(commandstohandle[0])
        else:
            self.pick_commandnumber_add_to_pending(ProposalServerBatch(commandstohandle))
        self.issue_pending_commands()

    def send_reject_to_client(self, conn, clientcommandnumber):
        conn.send(create_message(MSG_CLIENTREPLY, self.me,
                                 {FLD_REPLY: '',
                                  FLD_REPLYCODE: CR_REJECTED,
                                  FLD_INRESPONSETO: clientcommandnumber}))
    def msg_clientbatch(self, conn, msg):
        self.msg_clientrequest(conn, msg)

    def msg_clientrequest(self, conn, msg):
        """called holding self.lock
        handles clientrequest message received according to replica's state
        - if not leader: reject
        - if leader: add connection to client connections and handle request"""
        if not self.stateuptodate:
            return
        if self.isleader:
            # if leader, handle the clientrequest
            if self.token and msg.token != self.token:
                if self.debug: self.logger.write("Error", "Security Token mismatch.")
                self.send_reject_to_client(conn, msg.command.clientcommandnumber)
            else:
                if self.debug: self.logger.write("State", "I'm the leader, handling the request.")
                self.handle_client_command(msg.command, msg.sendcount,
                                           prepare=self.leader_initializing)
        else:
            leaderalive, leader = self.leader_is_alive()
            if leaderalive and leader != self.me:
                if self.debug: self.logger.write("State", "Not Leader: Rejecting CLIENTREQUEST")
                self.send_reject_to_client(conn, msg.command.clientcommandnumber)
            elif leader == self.me:
                # check if should become leader
                self.become_leader()
                if self.token and msg.token != self.token:
                    if self.debug: self.logger.write("Error", "Security Token mismatch.")
                    self.send_reject_to_client(conn, msg.command.clientcommandnumber)
                else:
                    self.handle_client_command(msg.command, msg.sendcount, prepare=self.leader_initializing)
            elif not leaderalive and self.find_leader() == self.me:
                # check if should become leader
                self.become_leader()
                # take old leader out of the configuration
                if self.debug: self.logger.write("State",
                                                 "Taking old leader out of the configuration.")
                delcommand = self.create_delete_command(leader)
                if delcommand not in self.pendingmetacommands:
                    with self.pendingmetalock:
                        self.pendingmetacommands.add(delcommand)
                    self.pick_commandnumber_add_to_pending(delcommand)
                    for i in range(WINDOW):
                        noopcommand = self.create_noop_command()
                        self.pick_commandnumber_add_to_pending(noopcommand)
                    self.issue_pending_commands()
                if self.token and msg.token != self.token:
                    if self.debug: self.logger.write("Error", "Security Token mismatch.")
                    self.send_reject_to_client(conn, msg.command.clientcommandnumber)
                else:
                    self.handle_client_command(msg.command, msg.sendcount, prepare=self.leader_initializing)

    def msg_clientrequest_batch(self, msgconnlist):
        """called holding self.lock
        handles clientrequest messages that are batched together"""
        if self.isleader:
            # if leader, handle the clientrequest
            for (msg,conn) in msgconnlist:
                if self.token and msg.token != self.token:
                    if self.debug: self.logger.write("Error", "Security Token mismatch.")
                    self.send_reject_to_client(conn, msg.command.clientcommandnumber)
                    msgconnlist.remove((msg,conn))
            self.handle_client_command_batch(msgconnlist, prepare=self.leader_initializing)
        else:
            leaderalive, leader = self.leader_is_alive()
            if leaderalive and leader != self.me:
                if self.debug: self.logger.write("State", "Not Leader: Rejecting all CLIENTREQUESTS")
                for (msg,conn) in msgconnlist:
                    self.send_reject_to_client(conn, msg.command.clientcommandnumber)
            elif leader == self.me:
                # check if should become leader
                self.become_leader()
                for (msg,conn) in msgconnlist:
                    if self.token and msg.token != self.token:
                        if self.debug: self.logger.write("Error", "Security Token mismatch.")
                        self.send_reject_to_client(conn, msg.command.clientcommandnumber)
                        msgconnlist.remove((msg,conn))
                self.handle_client_command_batch(msgconnlist, prepare=self.leader_initializing)
            elif not leaderalive and self.find_leader() == self.me:
                self.become_leader()
                # take old leader out of the configuration
                if self.debug: self.logger.write("State",
                                                 "Taking old leader out of the configuration.")
                delcommand = self.create_delete_command(leader)
                if delcommand not in self.pendingmetacommands:
                    with self.pendingmetalock:
                        self.pendingmetacommands.add(delcommand)
                    self.pick_commandnumber_add_to_pending(delcommand)
                    for i in range(WINDOW):
                        noopcommand = self.create_noop_command()
                        self.pick_commandnumber_add_to_pending(noopcommand)
                for (msg,conn) in msgconnlist:
                    if self.token and msg.token != self.token:
                        if self.debug: self.logger.write("Error", "Security Token mismatch.")
                        self.send_reject_to_client(conn, msg.command.clientcommandnumber)
                        msgconnlist.remove((msg,conn))
                self.handle_client_command_batch(msgconnlist, prepare=self.leader_initializing)

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
                givenresult = pickle.dumps(e)
                clientreplycode = CR_EXCEPTION
                send_result_to_client = True
                unblocked = {}
        except (TypeError, AttributeError) as t:
            if self.debug: self.logger.write("Execution Error", "command not supported: %s" % (command))
            if self.debug: self.logger.write("Execution Error", "%s" % str(t))
            givenresult = 'COMMAND NOT SUPPORTED'
            clientreplycode = CR_EXCEPTION
            unblocked = {}
            send_result_to_client = True
        if commandname not in METACOMMANDS and send_result_to_client:
            self.send_reply_to_client(clientreplycode, givenresult, command)

    def msg_clientreply(self, conn, msg):
        """this only occurs in response to commands initiated by the shell"""
        return

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
        if self.debug: self.logger.write("State", "Proposing command: %d:%s with ballotnumber %s"
                          % (givencommandnumber,givenproposal,str(recentballotnumber)))
        # Since we never propose a commandnumber that is beyond the window,
        # we can simply use the current acceptor set here
        prc = ResponseCollector(self.groups[NODE_ACCEPTOR], recentballotnumber,
                                givencommandnumber, givenproposal)
        if len(prc.acceptors) == 0:
            if self.debug: self.logger.write("Error", "There are no Acceptors, returning!")
            self.remove_from_proposals(givencommandnumber)
            self.add_to_pendingcommands(givencommandnumber, givenproposal)
            return
        self.outstandingproposes[givencommandnumber] = prc
        propose = create_message(MSG_PROPOSE, self.me,
                                 {FLD_BALLOTNUMBER: recentballotnumber,
                                  FLD_COMMANDNUMBER: givencommandnumber,
                                  FLD_PROPOSAL: givenproposal,
                                  FLD_SERVERBATCH: isinstance(givenproposal, ProposalServerBatch)})
        self.send(propose, group=prc.acceptors)

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
        if self.debug: self.logger.write("State", "Preparing command: %d:%s with ballotnumber %s"
                          % (givencommandnumber, givenproposal,str(newballotnumber)))
        prc = ResponseCollector(self.groups[NODE_ACCEPTOR], newballotnumber,
                                givencommandnumber, givenproposal)
        if len(prc.acceptors) == 0:
            if self.debug: self.logger.write("Error", "There are no Acceptors, returning!")
            self.remove_from_proposals(givencommandnumber)
            self.add_to_pendingcommands(givencommandnumber, givenproposal)
            return
        self.outstandingprepares[newballotnumber] = prc
        prepare = create_message(MSG_PREPARE, self.me,
                                 {FLD_BALLOTNUMBER: newballotnumber})
        self.send(prepare, group=prc.acceptors)

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
        if msg.inresponseto in self.outstandingprepares:
            prc = self.outstandingprepares[msg.inresponseto]
            prc.receivedcount += 1
            prc.receivedfrom.add(conn.peerid)
            if self.debug: self.logger.write("Paxos State",
                                             "got an accept for ballotno %s commandno %s proposal %s with %d out of %d"
                                             % (prc.ballotnumber, prc.commandnumber, prc.proposal, prc.receivedcount, prc.ntotal))
            assert msg.ballotnumber == prc.ballotnumber, "[%s] MSG_PREPARE_ADOPTED cannot have non-matching ballotnumber" % self
            # add all the p-values from the response to the possiblepvalueset
            if msg.pvalueset is not None:
                prc.possiblepvalueset.union(msg.pvalueset)

            if prc.receivedcount >= prc.nquorum:
                if self.debug: self.logger.write("Paxos State", "suffiently many accepts on prepare!")
                # take this response collector out of the outstanding prepare set
                del self.outstandingprepares[msg.inresponseto]
                # choose pvalues with distinctive commandnumbers and highest ballotnumbers
                pmaxset = prc.possiblepvalueset.pmax()
                for commandnumber,proposal in pmaxset.iteritems():
                    self.add_to_proposals(commandnumber, proposal)
                # If the commandnumber we were planning to use is overwritten
                # we should try proposing with a new commandnumber
                if self.proposals[prc.commandnumber] != prc.proposal:
                    self.pick_commandnumber_add_to_pending(prc.proposal)
                    self.issue_pending_commands()
                for chosencommandnumber,chosenproposal in self.proposals.iteritems():
                    # send proposals for every outstanding proposal that is collected
                    if self.debug: self.logger.write("Paxos State", "Sending PROPOSE for %d, %s" % (chosencommandnumber, chosenproposal))
                    newprc = ResponseCollector(prc.acceptors, prc.ballotnumber, chosencommandnumber, chosenproposal)
                    self.outstandingproposes[chosencommandnumber] = newprc
                    propose = create_message(MSG_PROPOSE, self.me,
                                             {FLD_BALLOTNUMBER: prc.ballotnumber,
                                              FLD_COMMANDNUMBER: chosencommandnumber,
                                              FLD_PROPOSAL: chosenproposal,
                                              FLD_SERVERBATCH: isinstance(chosenproposal, ProposalServerBatch)})
                    self.send(propose, group=newprc.acceptors)
                # As leader collected all proposals from acceptors its state is up-to-date
                # and it is done initializing
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
        if msg.inresponseto in self.outstandingprepares:
            prc = self.outstandingprepares[msg.inresponseto]
            if self.debug: self.logger.write("Paxos State", "got a reject for ballotno %s commandno %s proposal %s with %d out of %d" % (prc.ballotnumber, prc.commandnumber, prc.proposal, prc.receivedcount, prc.ntotal))
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
            self.pick_commandnumber_add_to_pending(prc.proposal)
            self.issue_pending_commands()

    def msg_propose_accept(self, conn, msg):
        """MSG_PROPOSE_ACCEPT is handled only if it belongs to an outstanding MSG_PREPARE,
        otherwise it is discarded.
        When MSG_PROPOSE_ACCEPT is received, the corresponding ResponseCollector is retrieved
        and its state is updated accordingly.

        State Updates:
        - increment receivedcount
        - if receivedcount is greater than the quorum size, PROPOSE STAGE is successful.
        -- remove the old ResponseCollector from the outstanding prepare set
        -- create MSG_PERFORM: message carries the chosen commandnumber and proposal.
        -- send MSG_PERFORM to all Replicas and Leaders
        -- execute the command
        """
        if msg.commandnumber in self.outstandingproposes:
            prc = self.outstandingproposes[msg.commandnumber]
            if msg.inresponseto == prc.ballotnumber:
                prc.receivedcount += 1
                prc.receivedfrom.add(conn.peerid)
                if self.debug: self.logger.write("Paxos State",
                                  "got an accept for proposal ballotno %s commandno %s proposal %s making %d out of %d accepts"
                                  % (prc.ballotnumber, prc.commandnumber, prc.proposal, prc.receivedcount, prc.ntotal))
                if prc.receivedcount >= prc.nquorum:
                    if self.debug: self.logger.write("Paxos State", "Agreed on %s" % str(prc.proposal))
                    # take this response collector out of the outstanding propose set
                    self.add_to_proposals(prc.commandnumber, prc.proposal)
                    # delete outstanding messages that caller does not need to check for anymore
                    del self.outstandingproposes[msg.commandnumber]
                    # now we can perform this action on the replicas
                    performmessage = create_message(MSG_PERFORM, self.me,
                                                    {FLD_COMMANDNUMBER: prc.commandnumber,
                                                     FLD_PROPOSAL: prc.proposal,
                                                     FLD_SERVERBATCH: isinstance(prc.proposal, ProposalServerBatch),
                                                     FLD_CLIENTBATCH: isinstance(prc.proposal, ProposalClientBatch)})


                    if self.debug: self.logger.write("Paxos State", "Sending PERFORM!")
                    if len(self.groups[NODE_REPLICA]) > 0:
                        self.send(performmessage, group=self.groups[NODE_REPLICA])
                    if len(self.groups[NODE_NAMESERVER]) > 0:
                        self.send(performmessage, group=self.groups[NODE_NAMESERVER])
                    self.perform(parse_message(performmessage), designated=True)
            if self.debug: self.logger.write("State", "returning from msg_propose_accept")

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
        if msg.commandnumber in self.outstandingproposes:
            prc = self.outstandingproposes[msg.commandnumber]
            if msg.inresponseto == prc.ballotnumber:
                if self.debug: self.logger.write("Paxos State", "got a reject for proposal ballotno %s commandno %s proposal %s still %d out of %d accepts" % \
                       (prc.ballotnumber, prc.commandnumber, prc.proposal, prc.receivedcount, prc.ntotal))
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
                if self.debug: self.logger.write("Paxos State", "There is another leader, backing off.")
                time.sleep(self.backoff)
                self.pick_commandnumber_add_to_pending(prc.proposal)
                self.issue_pending_commands()

    def ping_neighbor(self):
        """used to ping neighbors periodically"""
        while True:
            # Go through all peers in the view
            for gtype,group in self.groups.iteritems():
                for peer in group:
                    successid = 0
                    if peer == self.me:
                        continue
                    # Check nodeliveness
                    if peer in self.nodeliveness:
                        nosound = time.time() - self.nodeliveness[peer]
                    else:
                        nosound = (3*LIVENESSTIMEOUT)

                    if nosound <= LIVENESSTIMEOUT:
                        self.groups[peer.type][peer] = 0
                        continue
                    if (4*LIVENESSTIMEOUT) > nosound and nosound > LIVENESSTIMEOUT:
                        # Send PING to neighbor
                        if self.debug: self.logger.write("State", "Sending PING to %s" % str(peer))
                        pingmessage = create_message(MSG_PING, self.me)
                        successid = self.send(pingmessage, peer=peer)
                    if successid < 0 or nosound > (4*LIVENESSTIMEOUT):
                        # The neighbor is not responding
                        if self.debug: self.logger.write("State",
                                                         "Neighbor not responding")
                        # Mark the neighbor
                        self.groups[peer.type][peer] += 1
                        # Check if you should delete a node as leader
                        if self.isleader:
                            if self.debug: self.logger.write("State", "Deleting node %s" % str(peer))
                            delcommand = self.create_delete_command(peer)
                            if delcommand not in self.pendingmetacommands:
                                with self.pendingmetalock:
                                    self.pendingmetacommands.add(delcommand)
                                self.pick_commandnumber_add_to_pending(delcommand)
                                for i in range(WINDOW):
                                    noopcommand = self.create_noop_command()
                                    self.pick_commandnumber_add_to_pending(noopcommand)
                                issuemsg = create_message(MSG_ISSUE, self.me)
                                self.send(issuemsg, peer=self.me)
                        elif self.find_leader() == self.me:
                            if self.debug: self.logger.write("State",
                                                             "Becoming leader")
                            self.become_leader()
                            if self.debug: self.logger.write("State", "Deleting node %s" % str(peer))
                            delcommand = self.create_delete_command(peer)
                            if delcommand not in self.pendingmetacommands:
                                with self.pendingmetalock:
                                    self.pendingmetacommands.add(delcommand)
                                self.pick_commandnumber_add_to_pending(delcommand)
                                for i in range(WINDOW):
                                    noopcommand = self.create_noop_command()
                                    self.pick_commandnumber_add_to_pending(noopcommand)
                                issuemsg = create_message(MSG_ISSUE, self.me)
                                self.send(issuemsg, peer=self.me)

            with self.recentlyupdatedpeerslock:
                self.recentlyupdatedpeers = []
            time.sleep(LIVENESSTIMEOUT)

    def create_delete_command(self, node):
        mynumber = self.metacommandnumber
        self.metacommandnumber += 1
        nodename = node.addr + ":" + str(node.port)
        operationtuple = ("_del_node", node.type, nodename)
        command = Proposal(self.me, mynumber, operationtuple)
        return command

    def create_add_command(self, node):
        mynumber = self.metacommandnumber
        self.metacommandnumber += 1
        nodename = node.addr + ":" + str(node.port)
        operationtuple = ("_add_node", node.type, nodename)
        command = Proposal(self.me, mynumber, operationtuple)
        return command

    def create_noop_command(self):
        mynumber = self.metacommandnumber
        self.metacommandnumber += 1
        nooptuple = ("noop")
        command = Proposal(self.me, mynumber, nooptuple)
        return command

## SHELL COMMANDS
    def cmd_command(self, *args):
        """shell command [command]: initiate a new command."""
        try:
            cmdproposal = Proposal(self.me, random.randint(1,10000000), args[1:])
            self.handle_client_command(cmdproposal)
        except IndexError as e:
            print "command expects only one command: ", str(e)

    def cmd_goleader(self, args):
        """start Leader state"""
        self.become_leader()

    def cmd_showobject(self, args):
        """print replicated object information"""
        print self.object

    def cmd_info(self, args):
        """print next commandnumber to execute and executed commands"""
        print str(self)

    def cmd_proposals(self,args):
        """prints proposals"""
        for cmdnum,command in self.proposals.iteritems():
            print "%d: %s" % (cmdnum,str(command))

    def cmd_pending(self,args):
        """prints pending commands"""
        for cmdnum,command in self.pendingcommands.iteritems():
            print "%d: %s" % (cmdnum,str(command))

## TERMINATION METHODS
    def terminate_handler(self, signal, frame):
        self._graceexit()

    def _graceexit(self, exitcode=0):
        sys.stdout.flush()
        sys.stderr.flush()
        if hasattr(self, 'logger'): self.logger.close()
        os._exit(exitcode)

def main():
    replicanode = Replica()
    replicanode.startservice()
    signal.signal(signal.SIGINT, replicanode.terminate_handler)
    signal.signal(signal.SIGTERM, replicanode.terminate_handler)
    signal.pause()

if __name__=='__main__':
    main()
