class PValueSet():
    """PValueSet encloses a set of pvalues and supports corresponding
    set functions.
    """
    def __init__(self):
        self.pvalues = set()

    def remove(self,pvalue):
        """Removes given pvalue from the PValueSet"""
        if pvalue in self.pvalues:
            self.pvalues.remove(pvalue)

    def add(self,pvalue):
        """Adds given PValue to the PValueSet"""
        if pvalue not in self.pvalues:
            self.pvalues.add(pvalue)

    def add_highest(self,pvalue):
        """Adds given PValue to the PValueSet overwriting matching
        (commandnumber,proposal) if it exists
        """
        self.pvalues.add(pvalue)
        for oldpvalue in self.pvalues:
            if pvalue.commandnumber == oldpvalue.commandnumber and pvalue.proposal == oldpvalue.proposal:
                if pvalue.ballotnumber > oldpvalue.ballotnumber:
                    self.pvalues.remove(oldpvalue)
                    break
                    
    def union(self,otherpvalueset):
        """Unionizes the pvalues of given PValueSet with the pvalues of the PValueSet"""
        return self.pvalues | otherpvalueset.pvalues

    def pmax(self):
        """Returns a  mapping from command numbers to proposals with the highest ballotnumbers"""
        commandnumbers = [pvalue.commandnumber for pvalue in self.pvalues]
        print "Will do PMAX for commandnumbers", commandnumbers
        pmaxresult = {}
        for c in commandnumbers:
            maxballotnumberpvalue = PValue()
            for pvalue in self.pvalues:
                if pvalue.commandnumber == c and pvalue.ballotnumber > maxballotnumberpvalue.ballotnumber:
                    maxballotnumberpvalue = pvalue
            pmaxresult[c] = maxballotnumberpvalue.proposal
        return pmaxresult

    def __len__(self):
        """Returns the number of PValues in the PValueSet"""
        return len(self.pvalues)

    def __str__(self):
        """Returns PValueSet information"""
        temp = ''
        for pvalue in self.pvalues:
            temp += str(pvalue)+"\n"
        return temp

class PValue():
    """PValue encloses a ballotnumber, commandnumber and proposal.
    PValue is used to keep Paxos state in Acceptor and Leader nodes.
    """
    def __init__(self,ballotnumber=(0,0),commandnumber=0,proposal=None,serialpvalue=None):
        """Initialize PValue

        PValue State
        - ballotnumber: ballotnumber for the PValue
        - commandnumber: commandnumber for the PValue
        - proposal: proposal for the PValue
        """
        self.ballotnumber = ballotnumber
        self.commandnumber = commandnumber
        self.proposal = proposal

    def id(self):
        """Returns the id (ballotnumber:commandnumber:proposal) of the PValue"""
        return "%s:%d:%s" % (str(self.ballotnumber),self.commandnumber,self.proposal)

    def __hash__(self):
        """Returns the hashed id"""
        return hash(self.id())

    def __eq__(self, otherpvalue):
        """Equality function for two PValues.
        Returns True if given PValue is equal to PValue, False otherwise.
        """
        return self.ballotnumber == otherpvalue.ballotnumber and \
            self.commandnumber == otherpvalue.commandnumber and \
            self.proposal == otherpvalue.proposal
    
    def __str__(self):
        """Returns PValue information"""
        return 'PValue(%s,%d,%s)' % (str(self.ballotnumber),self.commandnumber,self.proposal)
