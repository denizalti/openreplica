'''
@author: deniz
@note: Initializes the ConCoord Runtime
@date: August 11, 2011
'''
from time import sleep,time
import os
import sys
import subprocess
import objectgenerator
import time

# The Initializer gets the subdomain, number of replicas to be initialized 
# from the Client along with the Client Coordination Object, starts the ConCoord system
# with required Nodes.
class Initializer():
    def __init__(self, subdomain, clientobjectfile, numreplicas):
        self._start_concoord(subdomain, clientobjectfile, numreplicas)

    def start_concoord(self, subdomain, clientobjectfile, numreplicas):
        replicaports = [6670, 6671, 6672]
        acceptorports = [6680, 6681, 6682]
        nameserverports = [6690, 6691, 6692]
        logfile = file("%s_log" % subdomain, 'w')
        bootstrapport = 6668
        bootstrap = '127.0.0.1:6668'
        # Start a bootstrap
        self.output("Starting bootstrap at %s" % str(bootstrapport))
        self._start_bootstrap(bootstrapport, clientobjectfile, logfile)
        time.sleep(2)
        # Start replicas
        for port in replicaports:
            self.output("Starting replica at %s" % str(port))
            self._start_replica(bootstrap, port, clientobjectfile, logfile)

        # Start nameservers
        for port in nameserverports:
            self.output("Starting nameserver at %s" % str(port))
            self._start_nameserver(bootstrap, port, logfile, subdomain)

        # Start acceptors
        for port in acceptorports:
            self.output("Starting acceptor at %s" % str(port))
            self._start_acceptor(bootstrap, port, logfile)
        
    def _start_bootstrap(self, port, object, logfile):
        phandle = subprocess.Popen(['python', 'replica.py', '-o', object, '-p', str(port), '-l', '-d'], shell=False, stdin=None, stdout=logfile, stderr=logfile)
        
    def _start_replica(self, bootstrap, port, object, logfile):
        # start a Replica as a background process
        phandle = subprocess.Popen(['python', 'replica.py', '-b', bootstrap, '-o', object, '-p', str(port), '-l', '-d'], shell=False, stdin=None, stdout=logfile, stderr=logfile)
        self.output("Replica started.")

    def _start_nameserver(self, bootstrap, port, logfile):
        # start a Nameserver Node as a background process
        phandle = subprocess.Popen(['python', 'nameserver.py', '-b', bootstrap, '-p', str(port), '-l', '-d'], shell=False, stdin=None, stdout=logfile, stderr=logfile)
        self.output("Nameserver started.")
            
    def _start_acceptor(self, bootstrap, port, logfile):
        phandle = subprocess.Popen(['python', 'acceptor.py', '-b', bootstrap, '-p', str(port), '-l', '-d'], shell=False, stdin=None, stdout=logfile, stderr=logfile)
        self.output("Acceptor started.")
        
    def output(self, text):
        print "[Admin] %s" % text
