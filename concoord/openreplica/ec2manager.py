'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Planet Lab Manager that handles operations on Planet Lab.
@copyright: See LICENSE
'''
import argparse
import sys, os, socket, os.path
import random, time
import subprocess, signal

parser = argparse.ArgumentParser()

parser.add_argument("-h", "--host", action="store", dest="host",
                    help="username@hostname required to connect to the node")
parser.add_argument("-d", "--debug", action="store_true", dest="debug", default=False,
                    help="debug on/off")
args = parser.parse_args()

class EC2Manager():
    def __init__(self, host=args.host, debug=args.debug):
        self.host = host
        self.debug = debug
        print self._tryconnect()
        print "Done"

    def _tryconnect(self):
        cmd = ["ssh", self.host, "ls"]
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

    def download(self, remote, local):
        cmd = "scp " + self.host + ":" + remote + " "+ local
        rtv = os.system(cmd)
        return rtv

    def executecommandall(self, command, wait=True):
        pipedict = {}
        for node in self.nodes:
            cmd = ["ssh", self.host, command]
            pipe = self._issuecommand(cmd)
            if wait:
                pipedict[pipe] = pipe.communicate()
        if wait:
            return (self._waitforall(pipedict.keys()) == 0, pipedict)
        return

    def executecommandone(self, node, command, wait=True):
        cmd = ["ssh", "self.host", command]
        pipe = self._issuecommand(cmd)
        if wait:
            pipe.poll()
            stdout,stderr = pipe.communicate()
            return (self._waitforall([pipe]) == 0, (stdout,stderr))
        return pipe

    def uploadall(self, local, remote=""):
        pipelist = []
        for node in self.nodes:
            cmd = ["scp", local, self.host + ":" + remote]
            if os.path.isdir(local):
                cmd.insert(1, "-r")
            pipe = self._issuecommand(cmd)
            pipelist.append(pipe)
        return self._waitforall(pipelist) == 0

    def uploadone(self, node, local, remote=""):
        cmd = ["scp", local, self.host + ":" + remote]
        if os.path.isdir(local):
            cmd.insert(1, "-r")
        pipe = self._issuecommand(cmd)
        return self._waitforall([pipe]) == 0
