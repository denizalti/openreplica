class Block():
    """Lock object that supports following functions:
    - lock: locks the object
    - trylock: tries locking the object
    - unlock: unlocks the object
    - state: returns the state of the object
    """
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
        return self.locked
    
    def __str__(self):
        return "Locked: ", self.locked
        
    
        
        
