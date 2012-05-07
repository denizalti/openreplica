"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example stack
@copyright: See LICENSE
"""
class Stack:
    def __init__(self, **kwargs):
        self.stack = []
        
    def append(self, item, **kwargs):
        self.stack.append(item)
        
    def pop(self, **kwargs):
        self.stack.pop()

    def get_size(self, **kwargs):
        return len(self.stack)

    def get_stack(self, **kwargs):
        return self.stack

    def __str__(self, **kwargs):
        return self.stack
        
    
        
        
