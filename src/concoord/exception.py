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
    def __init__(self, value=''):
        self.value = value

    def __str__(self):
        return str(self.value)

class ConnectionError(ConCoordException):
    """Connection cannot be established"""
    def __init__(self, value=''):
        self.value = value

    def __str__(self):
        return str(self.value)

class BlockingReturn(ConCoordException):
    """Blocking Return"""
    def __init__(self, returnvalue=None):
        self.returnvalue = returnvalue

    def __str__(self):
        return str(self.returnvalue)

class UnblockingReturn(ConCoordException):
    """Unblocking Return"""
    def __init__(self, returnvalue=None, unblockeddict={}):
        self.returnvalue = returnvalue
        self.unblocked = unblockeddict

    def __str__(self):
        return str(self.returnvalue) + " ".join(unblockeddict.keys())
