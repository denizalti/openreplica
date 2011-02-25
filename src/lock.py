class Block():
    def __init__(self):
        self.locked = False

    def lock(self, args):
        if self.locked == True:
            return "FAILURE"
        else:
            self.locked = True
            return "block locked"
        
    def trylock(self, args):
        pass
        
    def unlock(self, args):
        self.locked = False
        return "block unlocked"
        
    def state(self, args):
        return self.lock
    
    def __str__(self):
        return self.lock
        
    
        
        
