'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Planet Lab Manager that handles operations on Planet Lab.
@date: August 1, 2011
@copyright: See LICENSE
'''
import sys, os, socket, os.path
import random, time
import subprocess, signal
from concoord.objects.openreplicacoordobj import OpenReplicaCoord
USERNAME="username"
USERKEYFILE = "hostprivatekey"
NODESFILE= "nodes"

with open(NODESFILE, 'r') as f:
    all_nodes = []
    for node in f.readlines():
        node = node.strip()
        all_nodes.append(node)

class PLConnection():
    def __init__(self, num=0, nodecheckers=None, nodes=[]):
        self.procs = []
        if num == 0 and len(nodes) == 0:
            self.nodes = []
            return
        if len(nodes) > 0:
            self.nodes = nodes
        else:
            self.nodes = []
            random.shuffle(all_nodes)
            all_nodes.append(all_nodes.pop(0))
            for pickednode in all_nodes:
                pickednode = socket.gethostbyname(pickednode) #Convert to IP addr
                if self._tryconnect(pickednode):
                    successful = nodecheckers is not None
                    if nodecheckers:
                        for nodechecker in nodecheckers:
                            successful = successful and nodechecker(self, pickednode)[0]
                    if successful:
                        self.nodes.append(pickednode)
                        if len(self.nodes) == num:
                            return
            raise ValueError
        
    def __len__(self):
        return len(self.nodes)

    def _getrandomnode(self):
        return all_nodes[random.randint(0, len(all_nodes)-1)]

    def _tryconnect(self, node):
        host = USERNAME + "@" + node
        cmd = ["ssh", "-i", USERKEYFILE, "-o", "StrictHostKeyChecking=no", host, "ls"]
        return self._system(cmd, timeout=20) == 0

    def _system(self, cmd, timeout=300):
        p = self._issuecommand(cmd)
        self.procs.append(p)
        return self._waitforall([p], timeout)

    def _issuecommand(self, cmd):
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return p

    def _waitforall(self, subprocesslist, timeout=300):
        start = time.time()
        while len(subprocesslist) > 0:
            todo = []
            for subprocess in subprocesslist:
                rtv = subprocess.poll()
                if rtv is None:
                    todo.append(subprocess)
                else:
                    self.procs.remove(subprocess)
            if len(todo) > 0:
                time.sleep(0.1)
                now = time.time()
                if now - start > timeout:
                    for p in todo:
                        os.kill(p.pid, signal.SIGKILL)
                        os.waitpid(p.pid, os.WNOHANG)
                        self.procs.remove(p)
                    return -len(todo)
            subprocesslist = todo
        return 0

    def getHosts(self):
        return self.nodes

    def download(self, remote, local):
        host = USERNAME + "@" + self.nodes[0]
        cmd = "scp " + host + ":" + remote + " "+ local
        rtv = os.system(cmd)
        return rtv

    def executecommandall(self, command, wait=True):
        procdict = {}
        for node in self.nodes:
            cmd = ["ssh", "-i", USERKEYFILE, "-o", "StrictHostKeyChecking=no", USERNAME + "@" + node, command]
            proc = self._issuecommand(cmd)
            self.procs.append(proc)
            if wait:
                procdict[proc] = proc.communicate()
        if wait:
            return (self._waitforall(procdict.keys()) == 0, procdict)
        return

    def executecommandone(self, node, command, wait=True):
        cmd = ["ssh", "-i", USERKEYFILE, "-o", "StrictHostKeyChecking=no", USERNAME + "@" + node, command]
        proc = self._issuecommand(cmd)
        self.procs.append(proc)
        if wait:
            stdout,stderr = proc.communicate()
            return (self._waitforall([proc]) == 0, (stdout,stderr))
        return proc

    def uploadall(self, local, remote=""):
        proclist = []
        for node in self.nodes:
            cmd = ["scp", "-i", USERKEYFILE, "-o", "StrictHostKeyChecking=no", local, USERNAME + "@" + node + ":" + remote]
            if os.path.isdir(local):
                cmd.insert(1, "-r")
            proc = self._issuecommand(cmd)
            self.procs.append(proc)
            proclist.append(proc)
        return self._waitforall(proclist) == 0
        
    def uploadone(self, node, local, remote=""):
        cmd = ["scp", "-i", USERKEYFILE, "-o", "StrictHostKeyChecking=no", local, USERNAME + "@" + node + ":" + remote]
        if os.path.isdir(local):
            cmd.insert(1, "-r")
        proc = self._issuecommand(cmd)
        self.procs.append(proc)
        return self._waitforall([proc]) == 0
