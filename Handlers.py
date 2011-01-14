from Generators import *
# MESSAGE HANDLERS
class Handlers():
    def handle_helo(self,msg):
        print "DEBUG: received HELO msg"
        # When a HELO msg is received, it indicates that the node is a bootstrap node
        # So the Node receiving the HELO message should start the process for
        # reaching consensus
        n = HighestBallotNumber
        data = n
        msggenerator = getattr(Generators,"create_prep")
        msg = msggenerator(Generators,data)
        #prep_replies = neighborhoodSet.broadcast(msg)
        # Here broadcast returns (n,v) pairs received.
    
    def handle_prep(self,msg):
        print "DEBUG: received PREP msg"
        # When a PREPare msg is received, it indicates that the node is an acceptor
        # The following scenarios can apply:
        # 1) The proposal number N is greater than any previous proposal number: Acpt(LastValueAccepted)
        # 2) The proposal number N is less than a previous proposal number: Rjct()
    
    def handle_prop(self,msg):
        print "DEBUG: received PROP msg"
        # When a PROPose msg is received, it indicates that the proposer is proposing a value
        # The following scenarios can apply:
        # 1) The PROPose msg is for a proposal that has not been rejected: Acpt(LastValueAccepted)
        # 2) The PROPose msg is for a proposal that has been rejected: Rjct()
    
    def handle_acpt(self,msg):
        print "DEBUG: received ACPT msg"
    
    def handle_rjct(self,msg):
        print "DEBUG: received RJCT msg"
        
    def handle_cmmt(self,msg):
        print "DEBUG: received CMMT msg"
    
    def handle_done(self,msg):
        print "DEBUG: received DONE msg"
    
    def handle_rmve(self,msg):
        print "DEBUG: received RMVE msg"
    
    def handle_ping(self,msg):
        print "DEBUG: received PING msg"
    
    def handle_errr(self,msg):
        print "DEBUG: received ERRR msg"