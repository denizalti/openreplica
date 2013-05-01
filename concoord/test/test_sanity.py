"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Value object to test concoord implementation
@copyright: See LICENSE
"""
class TestSanity():
    def __init__(self):
        self.value = 10**6
        self.counter = 0

    def add_10_percent(self):
        self.value *= 1.1
        self.counter += 1
        return self.counter

    def subtract_10000(self):
        self.value -= 10**4
        self.counter += 1
        return self.counter

    def get_data(self):
        return (self.value, self.counter)

    def __str__(self):
        return "%d,%d" % (self.value, self.counter)
