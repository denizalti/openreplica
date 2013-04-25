"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example stack
@copyright: See LICENSE
"""
class Stack:
    def __init__(self):
        self.stack = []

    def append(self, item):
        self.stack.append(item)

    def pop(self):
        self.stack.pop()

    def get_size(self):
        return len(self.stack)

    def get_stack(self):
        return self.stack

    def __str__(self):
        return self.stack




