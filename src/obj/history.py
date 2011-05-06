class History():
    """Object to keep track of history in a system.
    Supports three functions:
    - write
    - append
    - read
    """
    def __init__(self):
        self.history = []
        
    def write(self, args):
        self.history = []
        self.history.append(args[0])
        
    def append(self, args):
        self.history.append(args[0])
        
    def read(self, args):
        return self.__str__()
        
    def __str__(self):
        return " ".join([str(e) for e in self.history])

        
    
        
        
