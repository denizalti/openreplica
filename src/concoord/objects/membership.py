"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example membership object
@copyright: See LICENSE
"""
class Membership():
    def __init__(self, **kwargs):
        self.members = set()

    def add(self, member, **kwargs):
        if member not in self.members:
            self.members.add(member)
        
    def remove(self, member, **kwargs):
        if member in self.members:
            self.members.remove(member)
        else:
            raise KeyError(member)
        
    def __str__(self, **kwargs):
        return " ".join([str(m) for m in self.members])
