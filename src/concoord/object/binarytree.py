"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Example binarytree
@copyright: See LICENSE
"""
class BinaryTree:
    def __init__(self):
        # initializes the root member
        self.root = None
    
    def _addNode(self, data):
        # creates a new node and returns it
        return BNode(data)

    def insert(self, root, data):
        # inserts a new data
        if root == None:
            # it there isn't any data
            # adds it and returns
            return self._addNode(data)
        else:
            # enters into the tree
            if data <= root.data:
                # if the data is less than the stored one
                # goes into the left-sub-tree
                root.left = self.insert(root.left, data)
            else:
                # processes the right-sub-tree
                root.right = self.insert(root.right, data)
            return root
        
    def lookup(self, root, target):
        # looks for a value into the tree
        if root == None:
            return False
        else:
            # if it has found it...
            if target == root.data:
                return True
            else:
                if target < root.data:
                    # left side
                    return self.lookup(root.left, target)
                else:
                    # right side
                    return self.lookup(root.right, target)

    def delete(self, root, target):
        if root == None or not self.lookup(root, target):
            return False
        else:
            if target == root.data:
                del root
            else:
                if target < root.data:
                    # left side
                    return self.delete(root.left, target)
                else:
                    # right side
                    return self.delete(root.right, target)
        
    def get_min(self, root):
        # goes down into the left
        # arm and returns the last value
        while(root.left != None):
            root = root.left
        return root.data

    def get_max(self, root):
        # goes down into the right
        # arm and returns the last value
        while(root.right != None):
            root = root.right
        return root.data

    def get_depth(self, root):
        if root == None:
            return 0
        else:
            # computes the two depths
            ldepth = self.get_depth(root.left)
            rdepth = self.get_depth(root.right)
            # returns the appropriate depth
            return max(ldepth, rdepth) + 1
            
    def get_size(self, root):
        if root == None:
            return 0
        else:
            return self.get_size(root.left) + 1 + self.get_size(root.right)

class BNode:
    def __init__(self, data):
        # initializes the data members
        self.left = None
        self.right = None
        self.data = data

    
        
        
