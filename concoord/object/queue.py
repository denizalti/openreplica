"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example queue
@copyright: See LICENSE
"""
import Queue

class Queue:
    def __init__(self, maxsize=0):
        self.queue = Queue.Queue(maxsize)

    def qsize(self):
        return self.queue.qsize()

    def empty(self):
        return self.queue.empty()

    def full(self):
        return self.queue.full()

    def put(self, item):
        return self.queue.put_nowait(item)

    def get(self):
        return self.queue.get_nowait()

    def __str__(self):
        return str(self.queue)
