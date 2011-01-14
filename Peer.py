
class Peer():
    def __init__(self,id,port,addr):
        self.port = port
        self.addr = addr
        self.ID = id
        
    def __str__(self):
        return 'PEER(%s, %s, %d)' % (self.ID, self.addr, self.port)
    

    
        
        
