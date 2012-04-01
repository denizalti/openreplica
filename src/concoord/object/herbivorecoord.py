"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Herbivore coordination object
@copyright: See LICENSE
"""
class HerbivoreCoord():
    def __init__(self, **kwargs):
        self._groups = {}

    def get_group(self, name, **kwargs):
        if name in self._groups:
            return self._groups[name]
        else:
            raise KeyError(name)

    def add_group(self, name, size, **kwargs):
        if name not in self._groups:
            self._groups[name] = Group(size)

    def remove_group(self, name, **kwargs):
        if name in self._groups:
            del self._groups[name]
        else:
            raise KeyError(name)

    def add_node_to_group(self, name, node, **kwargs):
        if name in self._groups:
            return self._groups[name].add_member(node)
        else:
            return KeyError(name)

    def remove_node_from_group(self, name, node, **kwargs):
        if name in self._groups:
            return self._groups[name].remove_member(node)
        else:
            raise KeyError(name)

    def __str__(self, **kwargs):
        return "\n".join([str(n)+': '+str(s) for n,s in self._groups.iteritems()])

class Group():
    def __init__(self, size):
        self._epoch = 1
        self._size = int(size)
        self._members = set()

    def add_member(self, member):
        if member not in self._members and not self.is_ready():
            self._members.add(member)
            return True
        else:
            return False

    def remove_member(self, member):
        if member in self._members:
            self._members.remove(member)
        else:
            raise KeyError(member)

    def is_ready(self):
        # The mesh is ready at this epoch if the size is
        # equal to the number of members that joined
        return len(self._members) == self._size

    def get_members(self):
        return self._members

    def get_size(self):
        return self._size

    def set_size(self, size):
        self._size = int(size)

    def get_epoch(self):
        return self._epoch

    def set_epoch(self, epoch):
        self._epoch = int(epoch)
        
    def __str__(self):
        t = "Epoch: %d " % self._epoch
        t += "Size: %d " % self._size
        t += "Members: "
        t += " ".join([str(m) for m in self._members])
        return t
