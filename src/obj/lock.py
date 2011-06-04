from concoord import DistributedLock

class Lock():
    """Block object that supports following functions:
    - acquire: locks the object
    - release: unlocks the object
    """
    def __init__(self):
        self.lock = DistributedLock()

    def acquire(self, _concoord_designated, _concoord_owner, _concoord_command):
        self.lock.acquire(_concoord_designated, _concoord_owner, _concoord_command)
        
    def release(self, _concoord_designated, _concoord_owner, _concoord_command):
        self.lock.release(_concoord_designated, _concoord_owner, _concoord_command)
    
    def __str__(self):
        return str(self.lock)
