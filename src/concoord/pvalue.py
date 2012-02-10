'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: PValue is used to keep Paxos state in Acceptor and Leader nodes.
@date: February 1, 2011
@copyright: See LICENSE
'''
class PValue():
    """PValue encloses a ballotnumber, commandnumber and proposal."""
    def __init__(self,ballotnumber=(0,0),commandnumber=0,proposal=None,serialpvalue=None):
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

class PValueSet():
    """PValueSet encloses a set of pvalues with the highest ballotnumber (always)
    and supports corresponding set functions.
    """
    def __init__(self):
        self.pvalues = {} # indexed by (commandnumber,proposal): pvalue
        
    def add(self, pvalue):
        """Adds given PValue to the PValueSet overwriting matching
        (commandnumber,proposal) if it exists and has a smaller ballotnumber
        """
        index = (pvalue.commandnumber,pvalue.proposal)
        if self.pvalues.has_key(index):
            if self.pvalues[index].ballotnumber < pvalue.ballotnumber:
                self.pvalues[index] = pvalue
        else:
            self.pvalues[index] = pvalue

    def remove(self, pvalue):
        """Removes given pvalue"""
        index = (pvalue.commandnumber,pvalue.proposal)
        del self.pvalues[index]

    def truncateto(self, commandnumber):
        """Truncates the history up to given commandnumber"""
        keytuples = self.pvalues.keys()
        allkeys = sorted(keytuples, key=lambda keytuple: keytuple[0])
        # Sanity checking
        lastkey = allkeys[0][0]
        candelete = True
        for (cmdno,proposal) in allkeys:
            if cmdno == lastkey:
                lastkey += 1
            else:
                candelete = False
                break
        # Truncating
        if not candelete:
            return False
        for (cmdno,proposal) in allkeys:
            if cmdno < commandnumber:
                del self.pvalues[(cmdno,proposal)]
        return True
    
    def union(self, otherpvalueset):
        """Unionizes the pvalues of givenPValueSet with the pvalues of the
        PValueSet overwriting the (commandnumber,proposal) pairs with lower
        ballotnumber
        """
        for candidate in otherpvalueset.pvalues.itervalues():
            self.add(candidate)

    def pmax(self):
        """Returns a mapping from command numbers to proposals with the highest ballotnumbers"""
        pmaxresult = {}
        for (commandnumber,proposal) in self.pvalues.keys():
            pmaxresult[commandnumber] = proposal
        return pmaxresult

    def __len__(self):
        """Returns the number of PValues in the PValueSet"""
        return len(self.pvalues)

    def __str__(self):
        """Returns PValueSet information"""
        return "\n".join(str(pvalue) for pvalue in self.pvalues.itervalues())
