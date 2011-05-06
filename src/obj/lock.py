class Lock():
    """Block object that supports following functions:
    - acquire: locks the object
    - release: unlocks the object
    """
    def __init__(self):
        self.locked = False

    def acquire(self, args, _paxi_designated, _paxi_client_cmdno, _paxi_me):
        if self.locked == True:
            paxi.return_outofband(_paxi_me, _paxi_client_cmdno, caller, paxi.RCODE_BLOCK_UNTIL_NOTICE)
            raise paxi.UnusualReturn
        else:
            self.locked = True
            return True
        
    def release(self, args, _paxi_designated, _paxi_client_cmdno, _paxi_me):
        if self.locked == True:
            self.locked = False
            return 0
        else:
            raise thread.error("release unlocked lock")
    
    def __str__(self):
        return self.locked
        
    
        
        
