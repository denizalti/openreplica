"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example queue
@copyright: See LICENSE
"""
from collections import deque
class Queue:
    def __init__(self):
        self.queue = deque([])
        
    def append(self, item):
        self.queue.append(item)
        
    def remove(self):
        self.queue.popleft()

    def get_size(self):
        return len(self.queue)

    def get_queue(self):
        return self.queue
        
    
        
        
