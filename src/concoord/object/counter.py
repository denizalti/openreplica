"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example counter
@copyright: See LICENSE
"""
class Counter:
    def __init__(self, **kwargs):
        self.value = 0
        
    def decrement(self, **kwargs):
        self.value -= 1

    def increment(self, **kwargs):
        self.value += 1

    def getvalue(self, **kwargs):
        return self.value
    
    def __str__(self, **kwargs):
        return "The counter value is %d" % self.value
