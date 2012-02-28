"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example log object
@copyright: See LICENSE
"""
class Log():
    def __init__(self, **kwargs):
        self.log = []
        
    def write(self, entry, **kwargs):
        self.log = []
        self.log.append(entry)
        
    def append(self, entry, **kwargs):
        self.log.append(entry)
        
    def read(self, **kwargs):
        return self.__str__()
        
    def __str__(self, **kwargs):
        return " ".join([str(e) for e in self.log])

        
    
        
        
