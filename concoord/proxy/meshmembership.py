"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: MeshMembership proxy
@copyright: See LICENSE
"""
from concoord.blockingclientproxy import ClientProxy

class MeshMembership():
    def __init__(self, bootstrap, timeout=60, debug=False, token=None):
        self.proxy = ClientProxy(bootstrap, timeout, debug, token)

    def __concoordinit__(self):
        return self.proxy.invoke_command('__init__')

    def get_group_members(self, gname):
        return self.proxy.invoke_command('get_group_members', gname)

    def get_group_epoch(self, gname):
        return self.proxy.invoke_command('get_group_epoch', gname)

    def get_group_state(self, gname):
        return self.proxy.invoke_command('get_group_state', gname)

    def add_group(self, gname, minsize):
        return self.proxy.invoke_command('add_group', gname, minsize)

    def remove_group(self, gname):
        return self.proxy.invoke_command('remove_group', gname)

    def approve_join(self, gname, node, epochno):
        return self.proxy.invoke_command('approve_join', gname, node, epochno)

    def wait(self, gname):
        return self.proxy.invoke_command('wait', gname)

    def check_member(self, gname, node):
        return self.proxy.invoke_command('check_member', gname, node)

    def notify_failure(self, gname, epoch, failednode):
        return self.proxy.invoke_command('notify_failure', gname, epoch, failednode)

    def __str__(self):
        return self.proxy.invoke_command('__str__')
