'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Common ConCoord exceptions.
@date: February 3, 2011
@copyright: See LICENSE
'''
class ConCoordException(Exception):
    """Abstract base class shared by all concoord exceptions"""
    pass

class AcceptorError(ConCoordException):
    """Not enough acceptors or not responding"""
    pass

class SyntaxError(ConCoordException):
    """input is malformed."""
    pass

class Timeout(ConCoordException):
    """The operation timed out."""
    pass

class BlockingReturn(ConCoordException):
    """Blocking Return"""
    def __init__(self, returnvalue):
        self.returnvalue = returnvalue

class UnblockingReturn(ConCoordException):
    """Unblocking Return"""
    def __init__(self, returnvalue, unblockeddict):
        self.returnvalue = returnvalue
        self.unblocked = unblockeddict
