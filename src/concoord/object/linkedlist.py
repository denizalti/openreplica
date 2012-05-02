"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example linked list
@copyright: See LICENSE
"""
class Node:
  def __init__(self, data):
    self.data = data
    self.next = None

class LinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
    
    def add(self, data):
        new_node = Node( data )

        if self.head == None:
            self.head = new_node
            
        if self.tail != None:
            self.tail.next = new_node
      
        self.tail = new_node

    def remove(self, index):
        prev = None
        node = self.head
        i = 0

        while ( node != None ) and ( i < index ):
            prev = node
            node = node.next
            i += 1

        if prev == None:
            self.head = node.next
        else:
            prev.next = node.next

    def get_list(self):
        temp = []
        node = self.head
        while node != None:
            temp.append(node.data)
            node = node.next
        return temp

    def get_size(self):
        return len(self.get_list())
