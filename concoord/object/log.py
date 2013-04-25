"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example log
@copyright: See LICENSE
"""
class Log():
    def __init__(self):
        self.log = []

    def write(self, entry):
        self.log = []
        self.log.append(entry)

    def append(self, entry):
        self.log.append(entry)

    def read(self):
        return self.__str__()

    def __str__(self):
        return " ".join([str(e) for e in self.log])





