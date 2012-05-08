"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example test object
@copyright: See LICENSE
"""
class Test():
    def __init__(self, **kwargs):
        self.__concoord_token = "TESTTOKEN"
        self.value = 10

    def getvalue(self, **kwargs):
        return self.value

    def setvalue(self, newvalue, **kwargs):
        self.value = int(newvalue)
    
    def __str__(self, **kwargs):
        return "The value is %d" % self.value
