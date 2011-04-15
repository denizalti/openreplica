"""common paxi exceptions"""

class PaxiException(Exception):
    """Abstract base class shared by all paxi exceptions"""
    pass

class AcceptorError(PaxiException):
    """Not enough acceptors or not responding"""
    pass

class SyntaxError(PaxiException):
    """input is malformed."""
    pass

class Timeout(PaxiException):
    """The operation timed out."""
    pass
