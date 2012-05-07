"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example queue
@copyright: See LICENSE
"""
class Queue:
    def __init__(self, **kwargs):
        self.queue = []
        
    def append(self, item, **kwargs):
        self.queue.append(item)
        
    def remove(self, **kwargs):
        self.queue.pop(0)

    def get_size(self, **kwargs):
        return len(self.queue)

    def get_queue(self, **kwargs):
        return self.queue

    def __str__(self, **kwargs):
        return self.queue

    
        
    
        
        
