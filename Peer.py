from utils import computeNodeID

class Peer():
    def __init__(self, addr, port, id):
        self.port = port
        self.addr = addr
        self.ID = id
        
    def __str__(self):
        return 'PEER(%s, %s, %d)' % (self.ID, self.addr, self.port)
    

    
        
        
