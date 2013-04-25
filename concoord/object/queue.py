"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example queue
@copyright: See LICENSE
"""
class Queue:
    def __init__(self):
        self.queue = []

    def append(self, item):
        self.queue.append(item)

    def remove(self):
        self.queue.pop(0)

    def get_size(self):
        return len(self.queue)

    def get_queue(self):
        return self.queue

    def __str__(self):
        return self.queue
