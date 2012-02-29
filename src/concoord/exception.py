'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Common ConCoord exceptions.
@copyright: See LICENSE
'''
class ConCoordException(Exception):
    """Abstract base class shared by all concoord exceptions"""
    def __init__(self, msg=''):
        self.msg = msg

class Timeout(ConCoordException):
    """The operation timed out."""
    pass

class BlockingReturn(ConCoordException):
    """Blocking Return"""
    def __init__(self, returnvalue=None):
        self.returnvalue = returnvalue

    def __str__(self):
        return "ConCoord BlockingReturn Exception: " + str(self.returnvalue)

class UnblockingReturn(ConCoordException):
    """Unblocking Return"""
    def __init__(self, returnvalue=None, unblockeddict={}):
        self.returnvalue = returnvalue
        self.unblocked = unblockeddict

    def __str__(self):
        return "ConCoord UnblockingReturn Exception: " + str(self.returnvalue) + " ".join(unblockeddict.keys())
