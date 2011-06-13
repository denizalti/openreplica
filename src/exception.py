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

class UnusualReturn(ConCoordException):
    """Unusual Return"""
    pass
