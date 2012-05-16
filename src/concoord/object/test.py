"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example test object
@copyright: See LICENSE
"""
class Test():
    def __init__(self, **kwargs):
        self.value = 10

    def getvalue(self, **kwargs):
        return self.value

    def setvalue(self, newvalue, **kwargs):
        self.value = newvalue
    
    def __str__(self, **kwargs):
        return "The value is %d" % self.value
