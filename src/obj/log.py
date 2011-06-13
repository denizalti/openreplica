class Log():
    """Shared Log Object that supports functions:
    - write
    - append
    - read
    """
    def __init__(self):
        self.history = []
        
    def write(self, args, **kwargs):
        entry = args[0]
        self.history = []
        self.history.append(entry)
        
    def append(self, args, **kwargs):
        entry = args[0]
        self.history.append(entry)
        
    def read(self, **kwargs):
        return self.__str__()
        
    def __str__(self):
        return " ".join([str(e) for e in self.history])

        
    
        
        
