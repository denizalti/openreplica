"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example test object
@copyright: See LICENSE
"""
class Test():
    def __init__(self):
        self.value = 10

    def getvalue(self):
        return self.value

    def setvalue(self, newvalue):
        self.value = newvalue
    
    def __str__(self):
        return "The value is %d" % self.value
