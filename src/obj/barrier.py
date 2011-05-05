import copy
import paxi
from threading import Lock

class Barrier():
    """Barrier object that supports following functions:
    - wait: takes a thread who wants to wait on the barrier
    - state: returns the state of the barrier
    """
    def __init__(self, number):
        self.limit = number
        self.current = 0
        self.members = []
        self.atomic = Lock()

    def wait(self, args, _paxi_designated, _paxi_client_cmdno, _paxi_me):
        with self.atomic:
            if self.current == self.limit:
                return "BARRIER FULL"
            self.current += 1
            self.members.append(args[0])
            if self.current == self.limit:
                everyone = copy.copy(self.members)
                self.current = 0
                self.members = []
                paxi.return_outofband(_paxi_me, _paxi_client_cmdno, everyone, paxi.RCODE_UNBLOCK)
                raise paxi.UnusualReturn
            else:
                paxi.return_outofband(_paxi_me, _paxi_client_cmdno, caller, paxi.RCODE_BLOCK_UNTIL_NOTICE)
                raise paxi.UnusualReturn
        
    def state(self, args):
        return self.__str__()
    
    def __str__(self):
        temp = "Limit: %d\nCurrent: %d\nMembers: "
        for member in self.members:
            temp += str(member) + " "
        return temp
        
    
        
        
