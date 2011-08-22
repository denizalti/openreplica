'''
@author: deniz
@note: Sanity checker for ConCoord
@date: August 11, 2011
'''
from optparse import OptionParser
from time import sleep,time
import os
import sys
import signal
import subprocess
import objectgenerator

parser = OptionParser(usage="usage: %prog -n name -a availability -f failuremodel -o object")
parser.add_option("-n", "--name", action="store", dest="name", help="name of ConCoord instance")
parser.add_option("-a", "--availability", action="store", dest="availability", help="availability requirement")
parser.add_option("-f", "--failuremodel", action="store", dest="failure", help="failure model")
parser.add_option("-o", "--object", action="store", dest="clientobject", help="client object")

(options, args) = parser.parse_args()

# The Administrator gets name for the instance, availability requirement and failure model
# from the Client along with the Client Coordination Object, starts the ConCoord system
# with necessary number of Replicas and returns a Client Proxy to the client along with the
# system address.
class ConCoordAdministrator():
    def __init__(self, name, availability, failuremodel, clientobject):
        self._start_concoord(name, availability, failuremodel, clientobject)

    def _start_concoord(self, name, availability, failuremodel, clientobject):
        replicaports = self._pick_replicas(availability, failuremodel)
        acceptorports = [6680, 6681, 6682]
        nameserverports = [6690,6691,6692]
        logfile = file("%s_log" % name, 'w')
        bootstrapport = 6668
        bootstrap = "127.0.0.1:6668"
        # Start a bootstrap
        self._start_bootstrap(bootstrapport, logfile)
        
        # Start replicas
        for port in replicaports:
            self._start_replica(bootstrap, port, logfile)

        # Start nameservers
        for port in nameserverports:
            self._start_nameserver(bootstrap, port, logfile)

        # Start acceptors
        for port in acceptorports:
            self._start_acceptor(bootstrap, port, logfile)

        # Create Client Proxy
        proxyhandle = objectgenerator.createproxyfromname(clientobject)
        

    def _start_bootstrap(self, port, logfile):
        phandle = subprocess.Popen(['python', 'replica.py', '-p', port, '-l', '-d'], shell=False, stdin=None, stdout=logfile, stderr=logfile)
        
    def _start_replica(self, bootstrap, port, logfile):
        # start a Replica as a background process
        phandle = subprocess.Popen(['python', 'replica.py', '-b', bootstrap, '-p', port, '-l', '-d'], shell=False, stdin=None, stdout=logfile, stderr=logfile)
        self.output("Replica started.")

    def _start_nameserver(self, bootstrap, port, logfile):
        # start a Nameserver Node as a background process
        phandle = subprocess.Popen(['python', 'nameserver.py', '-b', bootstrap, '-p', port, '-l', '-d'], shell=False, stdin=None, stdout=logfile, stderr=logfile)
        self.output("Nameserver started.")
            
    def _start_acceptor(self, bootstrap, port, logfile):
        phandle = subprocess.Popen(['python', 'acceptor.py', '-b', bootstrap, '-p', port, '-l', '-d'], shell=False, stdin=None, stdout=logfile, stderr=logfile)
        self.output("Acceptor started.")

    def _pick_replicas(availability, failuremodel):
        # XXX: Availability and Failure Model Code
        return [6670, 6671, 6672]

    def output(self, text):
        print "[Admin] %s" % text
    
def main():
    admin = ConCoordAdministrator(options.name, options.availability, options.failure, options.clientobject)
    
if __name__=='__main__':
    main()
