'''
@author: deniz
@note: Sanity checker for ConCoord
@date: August 11, 2011
'''
from optparse import OptionParser
from threading import Thread, RLock, Lock, Condition, Timer
from time import sleep,time
import os
import signal
import subprocess
import time
import random
import socket
import select
import copy
import fcntl

from enums import *
from utils import *
from node import *
from connection import ConnectionPool,Connection
from group import Group
from peer import Peer
from message import Message, PaxosMessage, HandshakeMessage, AckMessage, MessageInfo
from command import Command
from pvalue import PValue, PValueSet
from concoordprofiler import *

parser = OptionParser(usage="usage: %prog -r replicas -a acceptors -c clients")
parser.add_option("-r", "--replica", action="store", dest="numreplicas", type="int", default=1, help="number of replicas")
parser.add_option("-a", "--acceptor", action="store", dest="numacceptors", type="int", default=1, help="number of acceptors")
parser.add_option("-c", "--client", action="store", dest="numclients", type="int", default=1, help="number of clients")
parser.add_option("-i", "--clientinput", action="store", dest="clientinput", default="clientinputs/noop", help="client input file")

(options, args) = parser.parse_args()

# The Sanity Checker creates given number of Replicas
# Acceptors and Clients and runs multiple commands
# and compares the outputs of Replicas
class SanityChecker():
    def __init__(self, numreplicas, numacceptors, numclients, clientinput):
        self.replicacount = numreplicas
        self.acceptorcount = numacceptors
        self.clientcount = numclients
        self.clientinput = clientinput

        # lists to keep the processids of object 
        self.replicas = {}
        self.acceptors = {}
        self.clients = {}

        # rm old outputs create new output folder
        try:
            subprocess.call(['rm', '-rf', 'testoutput'])
        except:
            pass
        subprocess.call(['mkdir', 'testoutput'])
        
        # start nodes
        self.start_replicas()
        self.start_acceptors()
        self.start_clients()

        self.output("Replicas: %s" % str(self.replicas))
        self.output("Acceptors: %s" % str(self.acceptors))
        self.output("Clients: %s" % str(self.clients))
        sleep(5)
        self.kill_all()
        self.close_all_files()

    def start_replicas(self):
        # start each Replica as a background process
        fhandle = file("testoutput/replica0output", 'w')
        phandle = subprocess.Popen(['python', 'replica.py', '-l'], shell=False, stdin=None, stdout=fhandle, stderr=fhandle)
        self.replicas[phandle] = fhandle
        sleep(1)
        self.output("Replica 0 started.")
        for i in range(self.replicacount-1):
            fhandle = file("testoutput/replica%doutput" %i, 'w')
            phandle = subprocess.Popen(['python', 'replica.py', '-b', '127.0.0.1:6668', '-l'], shell=False, stdin=None, stdout=fhandle, stderr=fhandle)
            self.replicas[phandle] = fhandle
            sleep(0.5)
            self.output("Replica %d started." % i+1)
            
    def start_acceptors(self):
        for i in range(self.acceptorcount):
            fhandle = file("testoutput/acceptor%doutput" %i, 'w')
            phandle = subprocess.Popen(['python', 'acceptor.py', '-b', '127.0.0.1:6668', '-l'], shell=False, stdin=None, stdout=fhandle, stderr=fhandle)
            self.acceptors[phandle] = fhandle
            sleep(0.5)
            self.output("Acceptor %d started." % i)

    def start_clients(self):
        for i in range(self.clientcount):
            fhandle = file("testoutput/client%doutput" %i, 'w')
            phandle = subprocess.Popen(['python', 'noopclient.py', '-b', '127.0.0.1:6668'], shell=False,  stdin=None, stdout=fhandle, stderr=fhandle)
            self.clients[phandle] = fhandle
            self.output("Client %d started." % i)

    def close_all_files(self):
        fhandles = self.replicas.values() + self.acceptors.values() + self.clients.values()
        for fhandle in fhandles:
            fhandle.close()

        self.output("All files closed.")

    def kill_all(self):
        phandles = self.clients.keys() + self.acceptors.keys() + self.replicas.keys()
        for phandle in phandles:
            phandle.terminate()

        self.output("All processes killed.")
        
    def output(self, text):
        print "[Test] %s" % text
    
def main():
    tester = SanityChecker(numreplicas=options.numreplicas, numacceptors=options.numacceptors, numclients=options.numclients, clientinput=options.clientinput)
    
if __name__=='__main__':
    main()
