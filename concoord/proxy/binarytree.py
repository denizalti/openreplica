"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Binarytree proxy
@copyright: See LICENSE
"""
from concoord.clientproxy import ClientProxy
class BinaryTree:
    def __init__(self, bootstrap, timeout=60, debug=False, token=None):
        self.proxy = ClientProxy(bootstrap, timeout, debug, token)

    def __concoordinit__(self):
        return self.proxy.invoke_command('__init__')

    def add_node(self, data):
        return self.proxy.invoke_command('add_node', data)

    def insert(self, root, data):
        return self.proxy.invoke_command('insert', root, data)

    def find(self, root, target):
        return self.proxy.invoke_command('find', root, target)

    def delete(self, root, target):
        return self.proxy.invoke_command('delete', root, target)

    def get_min(self, root):
        return self.proxy.invoke_command('get_min', root)

    def get_max(self, root):
        return self.proxy.invoke_command('get_max', root)

    def get_depth(self, root):
        return self.proxy.invoke_command('get_depth', root)

    def get_size(self, root):
        return self.proxy.invoke_command('get_size', root)




