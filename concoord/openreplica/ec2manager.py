'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: EC2 Manager that handles operations on EC2.
@copyright: See LICENSE
'''
from threading import Thread
import sys, os, socket, os.path
import random, time
import subprocess, signal

VERSION = '1.0.2'

class EC2Manager():
    def __init__(self, nodes, sshkey, username):
        self.username = username
        # username
        if not self.username:
            print "There is no username. Add username."
            return
        # instances
        if nodes:
            self.instances = nodes.split(',')
        else:
            self.instances = []
            print "There are no instances listed. Add instances."
            return
        # key-pair filename
        self.sshkey = sshkey
        if self.sshkey:
            home = os.path.expanduser("~")
            cmd = ['ssh-add', home+'/.ssh/' + self.sshkey]
            self._waitforall([self._issuecommand(cmd)])
        else:
            print "There is no sshkey filename. Add sshkey filename."
            return
        self.alive = True

    def _tryconnect(self, host):
        cmd = ["ssh", host, "ls"]
        return self._system(cmd, timeout=20) == 0

    def _system(self, cmd, timeout=300):
        p = self._issuecommand(cmd)
        return self._waitforall([p], timeout)

    def _issuecommand(self, cmd):
        return subprocess.Popen(cmd)

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
        cmd = ["ssh", host, command]
        pipe = self._issuecommand(cmd)
        if wait:
            pipe.poll()
            stdout,stderr = pipe.communicate()
            return (self._waitforall([pipe]) == 0, (stdout,stderr))
        return pipe

    def download(self, remote, local):
        cmd = "scp " + self.host + ":" + remote + " "+ local
        rtv = os.system(cmd)
        return rtv

    def upload(self, host, node, local, remote=""):
        """upload concoord src to amazon instance"""
        cmd = ["scp", local, host + ":" + remote]
        if os.path.isdir(local):
            cmd.insert(1, "-r")
        pipe = self._issuecommand(cmd)
        return self._waitforall([pipe]) == 0

    def __str__(self):
        rstr = "Username: " + self.username + '\n'
        rstr += "SSH key file: " + self.sshkey + '\n'
        rstr += "Instances:\n"
        rstr += '\n'.join(self.instances)
        return rstr

# SHELL COMMANDS
    def cmd_help(self, args):
        """prints the commands that are supported
        by the corresponding Node."""
        print "Commands supported:"
        for attr in dir(self):
            if attr.startswith("cmd_"):
                print attr.replace("cmd_", "")

    def cmd_exit(self, args):
        """Changes the liveness state and dies"""
        self.alive = False
        self._graceexit()

    def cmd_info(self, args):
        """prints state of the EC2 instance."""
        print str(self)

    def cmd_install(self, args):
        """downloads and installs concoord to given instance"""
        if len(args) < 2:
            print "Instance public dns is required to install concoord."
            return
        instance = args[1]
        if instance not in self.instances:
            print "This instance is not in the configuration. Add and try again."
            return
        print "Downloading concoord.."
        cmd = ['ssh', self.username+'@'+instance, 'wget http://openreplica.org/src/concoord-'+VERSION+'.tar.gz']
        self._waitforall([self._issuecommand(cmd)])
        print "Installing concoord.."
        cmd = ['ssh', self.username+'@'+instance, 'tar xvzf concoord-'+VERSION+'.tar.gz']
        self._waitforall([self._issuecommand(cmd)])
        cmd = ['ssh', self.username+'@'+instance, 'cd concoord-'+VERSION'+ && python setup.py install']
        self._waitforall([self._issuecommand(cmd)])

    def get_user_input_from_shell(self):
        """Shell loop that accepts inputs from the command prompt and
        calls corresponding command handlers."""
        while self.alive:
            try:
                input = raw_input(">")
                if len(input) == 0:
                    continue
                else:
                    input = input.split()
                    mname = "cmd_%s" % input[0].lower()
                    try:
                        method = getattr(self, mname)
                    except AttributeError as e:
                        print "Command not supported: ", str(e)
                        continue
                    method(input)
            except KeyboardInterrupt:
                os._exit(0)
            except EOFError:
                return
        return

    def startservice(self):
        print "Type help to see all available commands"
        input_thread = Thread(target=self.get_user_input_from_shell, name='InputThread')
        input_thread.start()

## TERMINATION METHODS
    def terminate_handler(self, signal, frame):
        self._graceexit()

    def _graceexit(self, exitcode=0):
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(exitcode)
