from threading import Lock, Condition

class Command():
    """Command encloses a client, clientcommandnumber and command"""
    def __init__(self,client=None,clientcommandnumber=0,command=""):
        """Initialize Command

        Command State
        - client
        - clientcommandnumber: unique id for the command, specific to Client
                               doesn't affect paxos commandnumber
        - command: command to be executed
        """
        self.client = client
        self.clientcommandnumber = clientcommandnumber
        self.command = command
        # The following objects cannot be pickled.
#        self.lock = Lock()
#        self.done = False
#        self.donecondition = Condition(self.lock)

    def __hash__(self):
        """Returns the hashed command"""
        return hash(str(self.client)+str(self.clientcommandnumber)+str(self.command))

    def __eq__(self, othercommand):
        """Equality function for two Commands.
        Returns True if given Command is equal to Command, False otherwise.
        """
        return self.client == othercommand.client and \
            self.clientcommandnumber == othercommand.clientcommandnumber and \
            self.command == othercommand.command

    def __ne__(self, othercommand):
        """Non-equality function for two Commands.
        Returns True if given Command is not equal to Command, False otherwise.
        """
        return self.client != othercommand.client or \
            self.clientcommandnumber != othercommand.clientcommandnumber or \
            self.command != othercommand.command
    
    def __str__(self):
        """Returns Command information"""
        return 'Command(%s,%d,%s)' % (str(self.client),self.clientcommandnumber,self.command)
