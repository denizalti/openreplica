'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Planet Lab Manager that handles operations on Planet Lab.
@copyright: See LICENSE
'''
import sys, os, socket, os.path
import random, time
import subprocess, signal

class PLConnection():
    def __init__(self, num=0, nodecheckers=None, nodes=[], configdict={}):
        global USERNAME, USERKEYFILE, NODESFILE
        if not configdict:
            print "Configuration file is required."
            return

        USERNAME = configdict['USERNAME']
        USERKEYFILE = configdict['USERKEYFILE']
        NODESFILE = configdict['NODESFILE']

        # Read the list of nodes from the planetlab nodes file
        with open(NODESFILE, 'r') as f:
            all_nodes = []
            for node in f.readlines():
                node = node.strip()
                all_nodes.append(node)

        if num == 0 and len(nodes) == 0:
            self.nodes = []
            return
        if len(nodes) > 0:
            self.nodes = nodes
        else:
            self.nodes = []
            # Shuffle all nodes for pseudo load-balancing
            random.shuffle(all_nodes)
            all_nodes.append(all_nodes.pop(0))
            for pickednode in all_nodes:
                pickednode = socket.gethostbyname(pickednode) # Convert to IP addr
                if self._tryconnect(pickednode):
                    successful = nodecheckers is not None
                    if nodecheckers:
                        # Run the node checkers
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
        self._system(cmd, timeout=20) == 0
        return self._system(cmd, timeout=20) == 0

    def _system(self, cmd, timeout=300):
        p = self._issuecommand(cmd)
        return self._waitforall([p], timeout)

    def _issuecommand(self, cmd):
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return p

    def _waitforall(self, pipelist, timeout=300):
        start = time.time()
        while len(pipelist) > 0:
            todo = []
            for pipe in pipelist:
                rtv = pipe.poll()
                if rtv is None:
                    # not done
                    todo.append(pipe)
            if len(todo) > 0:
                time.sleep(0.1)
                now = time.time()
                if now - start > timeout:
                    # timeout reached
                    for p in todo:
                        os.kill(p.pid, signal.SIGKILL)
                        os.waitpid(p.pid, os.WNOHANG)
                    return -len(todo)
            pipelist = todo
        return 0

    def getHosts(self):
        return self.nodes

    def download(self, remote, local):
        host = USERNAME + "@" + self.nodes[0]
        cmd = "scp " + host + ":" + remote + " "+ local
        rtv = os.system(cmd)
        return rtv

    def executecommandall(self, command, wait=True):
        pipedict = {}
        for node in self.nodes:
            cmd = ["ssh", "-i", USERKEYFILE, "-o", "StrictHostKeyChecking=no", USERNAME + "@" + node, command]
            pipe = self._issuecommand(cmd)
            if wait:
                pipedict[pipe] = pipe.communicate()
        if wait:
            return (self._waitforall(pipedict.keys()) == 0, pipedict)
        return

    def executecommandone(self, node, command, wait=True):
        cmd = ["ssh", "-i", USERKEYFILE, "-o", "StrictHostKeyChecking=no", USERNAME + "@" + node, command]
        pipe = self._issuecommand(cmd)
        if wait:
            pipe.poll()
            stdout,stderr = pipe.communicate()
            return (self._waitforall([pipe]) == 0, (stdout,stderr))
        return pipe

    def uploadall(self, local, remote=""):
        pipelist = []
        for node in self.nodes:
            cmd = ["scp", "-i", USERKEYFILE, "-o", "StrictHostKeyChecking=no", local, USERNAME + "@" + node + ":" + remote]
            if os.path.isdir(local):
                cmd.insert(1, "-r")
            pipe = self._issuecommand(cmd)
            pipelist.append(pipe)
        return self._waitforall(pipelist) == 0

    def uploadone(self, node, local, remote=""):
        cmd = ["scp", "-i", USERKEYFILE, "-o", "StrictHostKeyChecking=no", local, USERNAME + "@" + node + ":" + remote]
        if os.path.isdir(local):
            cmd.insert(1, "-r")
        pipe = self._issuecommand(cmd)
        return self._waitforall([pipe]) == 0
