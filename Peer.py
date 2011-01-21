class Peer():
    def __init__(self,id,port,addr):
        self.port = port
        self.addr = addr
        self.id = id
        
    def serialize(self):
        return (self.id,self.addr,self.port)
        
    def __str__(self):
        return 'PEER(%s, %s, %d)' % (self.ID, self.addr, self.port)
    

    
        
        
