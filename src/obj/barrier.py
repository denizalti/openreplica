class Barrier():
    """Barrier object that supports following functions:
    - wait: takes a thread who wants to wait on the barrier
    - state: returns the state of the barrier
    """
    def __init__(self, number):
        self.limit = number
        self.current = 0
        self.members = []

    def wait(self, args):
        if self.current == self.limit:
            return "BARRIER FULL"
        self.current += 1
        self.members.append(args[0])
        if self.current == self.limit
            self._returnbarrier()
        
    def _returnbarrier(self):
        for client in self.members:
            return True # XXX
        self.current = 0
        self.members = []
        
    def state(self, args):
        return self.__str__()
    
    def __str__(self):
        temp = "Limit: %d\nCurrent: %d\nMembers: "
        for member in self.members:
            temp += str(member) + " "
        return temp
        
    
        
        
