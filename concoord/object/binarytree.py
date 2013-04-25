"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example binarytree
@copyright: See LICENSE
"""
class BinaryTree:
    def __init__(self):
        self.root = None

    def add_node(self, data):
        return Node(data)

    def insert(self, root, data):
        if root == None:
            return self.add_node(data)
        else:
            if data <= root.data:
                root.left = self.insert(root.left, data)
            else:
                root.right = self.insert(root.right, data)
            return root

    def find(self, root, target):
        if root == None:
            return False
        else:
            if target == root.data:
                return True
            else:
                if target < root.data:
                    return self.find(root.left, target)
                else:
                    return self.find(root.right, target)

    def delete(self, root, target):
        if root == None or not self.find(root, target):
            return False
        else:
            if target == root.data:
                del root
            else:
                if target < root.data:
                    return self.delete(root.left, target)
                else:
                    return self.delete(root.right, target)

    def get_min(self, root):
        while(root.left != None):
            root = root.left
        return root.data

    def get_max(self, root):
        while(root.right != None):
            root = root.right
        return root.data

    def get_depth(self, root):
        if root == None:
            return 0
        else:
            ldepth = self.get_depth(root.left)
            rdepth = self.get_depth(root.right)
            return max(ldepth, rdepth) + 1

    def get_size(self, root):
        if root == None:
            return 0
        else:
            return self.get_size(root.left) + 1 + self.get_size(root.right)

class Node:
    def __init__(self, data):
        self.left = None
        self.right = None
        self.data = data




