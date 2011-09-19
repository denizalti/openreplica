"""common concoord exceptions"""

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

class UnblockingReturn(ConCoordException):
    """Unblocking Return"""
    def __init__(self, returnvalue, unblockeddict):
        self.returnvalue = returnvalue
        self.unblocked = unblockeddict

class BlockingReturn(ConCoordException):
    """Blocking Return"""
    def __init__(self, returnvalue):
        self.returnvalue = returnvalue
