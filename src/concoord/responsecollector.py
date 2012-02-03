'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Class used to collect responses to both PREPARE and PROPOSE messages
@date: February 1, 2011
@copyright: See COPYING.txt
'''
from concoord.pvalue import PValue, PValueSet

class ResponseCollector():
    """ResponseCollector keeps the state related to both MSG_PREPARE and
    MSG_PROPOSE.
    """
    def __init__(self, acceptors, ballotnumber, commandnumber, proposal):
        """ResponseCollector state
        - ballotnumber: ballotnumber for the corresponding msg
        - commandnumber: commandnumber for the corresponding msg
        - proposal: proposal for the corresponding msg
        - acceptors: group of acceptor nodes for the corresponding msg
        - sent: msgids for the messages that have been sent
        - received: dictionary that keeps <peer:reply> mappings
        - ntotal: # of acceptornodes for the corresponding msg
        - nquorum: # of accepts needed for success
        - possiblepvalueset: Set of pvalues collected from acceptors
        """
        self.ballotnumber = ballotnumber
        self.commandnumber = commandnumber
        self.proposal = proposal
        self.acceptors = acceptors
        self.sent = []
        self.received = {}
        self.ntotal = len(self.acceptors)
        self.nquorum = self.ntotal/2+1
        self.possiblepvalueset = PValueSet()
