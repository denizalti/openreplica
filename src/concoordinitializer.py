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
import time

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
        nameserverports = [6690, 6691, 6692]
        logfile = file("%s_log" % name, 'w')
        bootstrapport = 6668
        bootstrap = '127.0.0.1:6668'
        # Start a bootstrap
        self.output("Starting bootstrap at %s" % str(bootstrapport))
        self._start_bootstrap(bootstrapport, clientobject, logfile)
        time.sleep(2)
        # Start replicas
        for port in replicaports:
            self.output("Starting replica at %s" % str(port))
            self._start_replica(bootstrap, port, clientobject, logfile)

        # Start nameservers
        for port in nameserverports:
            self.output("Starting nameserver at %s" % str(port))
            self._start_nameserver(bootstrap, port, logfile)

        # Start acceptors
        for port in acceptorports:
            self.output("Starting acceptor at %s" % str(port))
            self._start_acceptor(bootstrap, port, logfile)

        # Create Client Proxy
        proxyhandle = objectgenerator.createproxyfromname(clientobject)
        

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

    def _pick_replicas(self, availability, failuremodel):
        # XXX: Availability and Failure Model Code
        return [6670, 6671, 6672]

    def setup_connections(self, bootstrapport, replicaports, acceptorports, nameserverports):
        pass
        

    def output(self, text):
        print "[Admin] %s" % text
    
def main():
    admin = ConCoordAdministrator(options.name, options.availability, options.failure, options.clientobject)
    
if __name__=='__main__':
    main()
