"""
@author: denizalti, egs
@note: A Command is a request from a Client to the replicated object to carry out a method.
@date: February 1, 2011
"""
from threading import Lock, Condition

class Command():
    """This object represents the command sent by a client"""
    def __init__(self,client=None,clientcommandnumber=0,command=""):
        """Initialize Command

        Command State
        - client: the node that initiated this command.
        - clientcommandnumber: unique id for the command, specific to Client
                               doesn't affect paxos commandnumber
        - command: command to be executed
        """
        self.client = client
        self.clientcommandnumber = clientcommandnumber
        self.command = command

    def __hash__(self):
        # XXX wouldn't it be faster to avoid string creation and disposal by doing
        # XXX return hash(str(self.client))+hash(self.command) + self.clientcommandnumber
        return hash(str(self.client)+str(self.clientcommandnumber)+str(self.command))

    def __eq__(self, othercommand):
        """Two commands are identical when they're from the same client, the same request, with the same command number."""
        return self.client == othercommand.client and \
            self.clientcommandnumber == othercommand.clientcommandnumber and \
            self.command == othercommand.command

    def __ne__(self, othercommand):
        return not self.__eq__(othercommand)
    
    def __str__(self):
        return 'Command(%s,%d,%s)' % (str(self.client),self.clientcommandnumber,self.command)
