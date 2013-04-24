"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example counter
@copyright: See LICENSE
"""
class Counter
    def __concoordinit__(self):
        self.value = 0

    def decrement(self):
        self.value -= 1

    def increment(self):
        self.value += 1

    def getvalue(self):
        return self.value

    def __str__(self):
        return "The counter value is %d" % self.value
