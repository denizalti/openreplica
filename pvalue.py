
class pvalue():
    def __init__(self,ballot,command,proposal):
        self.ballot = ballot
        self.command = command
        self.proposal = proposal
        
    def __str__(self):
        return 'pvalue(%d, %d, %d)' % (self.ballot, self.command, self.proposal)
    

    
        
        
