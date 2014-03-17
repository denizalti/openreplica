'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Class used to collect responses to both PREPARE and PROPOSE messages
@copyright: See LICENSE
'''
from concoord.pvalue import PValueSet
from concoord.pack import PValue

class ResponseCollector():
    """ResponseCollector keeps the state related to both MSG_PREPARE and
    MSG_PROPOSE.
    """
    def __init__(self, replicas, ballotnumber, commandnumber, proposal):
        """ResponseCollector state
        - ballotnumber: ballotnumber for the corresponding msg
        - commandnumber: commandnumber for the corresponding msg
        - proposal: proposal for the corresponding msg
        - quorum: group of replica nodes for the corresponding msg
        - sent: msgids for the messages that have been sent
        - received: dictionary that keeps <peer:reply> mappings
        - ntotal: # of replica nodes for the corresponding msg
        - nquorum: # of accepts needed for success
        - possiblepvalueset: Set of pvalues collected from replicas
        """
        self.ballotnumber = ballotnumber
        self.commandnumber = commandnumber
        self.proposal = proposal
        self.quorum = replicas
        self.receivedcount = 0
        self.receivedfrom = set()
        self.ntotal = len(self.quorum)
        self.nquorum = self.ntotal/2+1
        self.possiblepvalueset = PValueSet()
