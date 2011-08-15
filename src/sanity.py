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

parser = OptionParser(usage="usage: %prog -r replicas -o coordinators -a acceptors -c clients -i clientinput")
parser.add_option("-r", "--replicas", action="store", dest="numreplicas", type="int", default=1, help="number of replicas")
parser.add_option("-o", "--coordinators", action="store", dest="numcoords", type="int", default=1, help="number of coordinators")
parser.add_option("-a", "--acceptors", action="store", dest="numacceptors", type="int", default=1, help="number of acceptors")
parser.add_option("-c", "--clients", action="store", dest="numclients", type="int", default=1, help="number of clients")
parser.add_option("-i", "--clientinput", action="store", dest="clientinput", default="clientinputs/noop", help="client input file")

(options, args) = parser.parse_args()

# The Sanity Checker creates given number of Replicas
# Acceptors and Clients and runs multiple commands
# and compares the outputs of Replicas
class SanityChecker():
    def __init__(self, numreplicas, numcoords, numacceptors, numclients, clientinput):
        self.replicacount = numreplicas
        self.coordinatorcount = numcoords
        self.acceptorcount = numacceptors
        self.clientcount = numclients
        self.clientinput = clientinput
        # keep the leader for failure test
        self.leader = None
        self.leaderfilename = '127.0.0.16668'
        # lists to keep the processids of object 
        self.replicas = {}
        self.acceptors = {}
        self.clients = {}
        self.coordinators = {}
        # rm old outputs create new output folder
        try:
            subprocess.call(['rm', '-rf', 'testoutput'])
        except:
            pass
        subprocess.call(['mkdir', 'testoutput'])
        subprocess.call(['mkdir', 'testoutput/rep'])
        subprocess.call(['mkdir', 'testoutput/obj'])

    def test1(self):
        # no failures
        # start nodes
        self._start_replicas()
        self._start_coordinators()
        self._start_acceptors()
        self._start_coordinatorclient()
        self.run(10)
        self._start_clients()
        # wait 20 seconds
        self.run(20)
        # terminate
        self._kill_all()

    def test2(self):
        # leader fails at t=10s+
        # start nodes
        self._start_replicas()
        self._start_coordinators()
        self._start_acceptors()
        self._start_coordinatorclient()
        self.run(10)
        self._start_clients()
        # wait 10 seconds
        self.run(10)
        # terminate
        self._kill_leader()
        # wait 10 seconds
        self.run(20)
        # terminate
        self._kill_all()

    def test3(self):
        # leader fails at t=10s+
        # leader recovers at t=30s+
        # start nodes
        self._start_replicas()
        self._start_coordinators()
        self._start_acceptors()
        self._start_coordinatorclient()
        self.run(10)
        self._start_clients()
        # wait 10 seconds
        self.run(10)
        # terminate
        self._kill_leader()
        # wait 20 seconds
        self.run(20)
        # recover leader
        self._restart_leader()
        # wait 20 seconds
        self.run(20)
        # terminate
        self._kill_all()

    def test1_check(self):
        success1 = self._check_file_equality('testoutput/rep')
        success2 = self._check_file_equality('testoutput/obj')
        success = success1 and success2
        if success == True:
            self.output("Test 1 PASSED!")
        else:
            self.output("Test 1 FAILED!")

    def test2_check(self):
        success1 = self._check_file_equality_with_leader_failure('testoutput/rep')
        success2 = self._check_file_equality_with_leader_failure('testoutput/obj')
        success = success1 and success2
        if success == True:
            self.output("Test 2 PASSED!")
        else:
            self.output("Test 2 FAILED!")

    def test3_check(self):
        success1 = self._check_file_equality_with_leader_failure('testoutput/rep')
        success2 = self._check_file_equality('testoutput/obj')
        success = success1 and success2
        if success == True:
            self.output("Test 3 PASSED!")
        else:
            self.output("Test 3 FAILED!")

    def run(self, seconds):
        sys.stdout.write("[Test] Running")
        sys.stdout.flush()
        for i in range(seconds):
            sys.stdout.write(".")
            sys.stdout.flush()
            sleep(1)
        sys.stdout.write("\n")
        sys.stdout.flush()

    def _check_file_equality_with_leader_failure(self, path):
        # check if all files under the given path are equal
        success = True
        replicafilestr = subprocess.check_output(['ls', path])
        replicafilelist = replicafilestr.strip('\n').split('\n')
        replicafilelist.remove(self.leaderfilename)
        for i in range(len(replicafilelist)-1):
            try:
                output = subprocess.check_output(['diff', '--brief', path+'/'+replicafilelist[i], path+'/'+replicafilelist[i+1]])
            except:
                success = False
        try:
            output = subprocess.check_output(['diff', '--brief', path+'/'+replicafilelist[0], path+'/'+self.leaderfilename])
            success = False
        except:
            pass
        return success

    def _check_file_equality(self, path):
        # check if all files under the given path are equal
        # apart from the failed leader
        success = True
        replicafilestr = subprocess.check_output(['ls', path])
        replicafilelist = replicafilestr.strip('\n').split('\n')
        print replicafilelist
        for i in range(len(replicafilelist)-1):
            try:
                output = subprocess.check_output(['diff', '--brief', 'testoutput/rep/'+replicafilelist[i], path+'/'+replicafilelist[i+1]])
            except:
                success = False
        return success
        
    def _start_replicas(self):
        # start each Replica as a background process
        self._start_leader()
        sleep(1)
        self.output("Replica 0 started.")
        for i in range(self.replicacount-1):
            rid = i+1
            fhandle = file("testoutput/replica%doutput" % rid, 'w')
            phandle = subprocess.Popen(['python', 'replica.py', '-b', '127.0.0.1:6668', '-l', '-d'], shell=False, stdin=None, stdout=fhandle, stderr=fhandle)
            self.replicas[phandle] = fhandle
            sleep(0.5)
            self.output("Replica %d started." % rid)
            
    def _start_acceptors(self):
        for i in range(self.acceptorcount):
            fhandle = file("testoutput/acceptor%doutput" %i, 'w')
            phandle = subprocess.Popen(['python', 'acceptor.py', '-b', '127.0.0.1:6668', '-l'], shell=False, stdin=None, stdout=fhandle, stderr=fhandle)
            self.acceptors[phandle] = fhandle
            sleep(0.5)
            self.output("Acceptor %d started." % i)

            
    def _start_coordinators(self):
        for i in range(self.coordinatorcount):
            fhandle = file("testoutput/coordinator%doutput" %i, 'w')
            phandle = subprocess.Popen(['python', 'coordinator.py', '-b', '127.0.0.1:6668', '-l'], shell=False, stdin=None, stdout=fhandle, stderr=fhandle)
            self.coordinators[phandle] = fhandle
            sleep(0.5)
            self.output("Coordinator %d started." % i)

    def _start_coordinatorclient(self):
        fhandle = file("testoutput/clientcoordoutput", 'w')
        phandle = subprocess.Popen(['python', 'client.py', '-b', '127.0.0.1:6668,127.0.0.1:6669,127.0.0.1:6670,127.0.0.1:6671', '-f', 'ports'], shell=False,  stdin=None, stdout=fhandle, stderr=fhandle)
        self.clients[phandle] = fhandle
        self.output("Coordinator Client started.")

    def _start_clients(self):
        for i in range(self.clientcount):
            fhandle = file("testoutput/client%doutput" %i, 'w')
            phandle = subprocess.Popen(['python', 'client.py', '-b', '127.0.0.1:6668,127.0.0.1:6669,127.0.0.1:6670,127.0.0.1:6671', '-f', '%s' % self.clientinput], shell=False,  stdin=None, stdout=fhandle, stderr=fhandle)
            self.clients[phandle] = fhandle
            self.output("Client %d started." % i)

    def _kill_leader(self):
        self.leader.terminate()
        self.replicas[self.leader].close()
        del self.replicas[self.leader]
        self.output("Leader killed.")

    def _start_leader(self):
        fhandle = file("testoutput/replica0output", 'w')
        phandle = subprocess.Popen(['python', 'replica.py', '-l', '-d'], shell=False, stdin=None, stdout=fhandle, stderr=fhandle)
        self.leader = phandle
        self.replicas[phandle] = fhandle

    def _restart_leader(self):
        fhandle = file("testoutput/replica0output", 'w')
        phandle = subprocess.Popen(['python', 'replica.py', '-b', '127.0.0.1:6669', '-l'], shell=False, stdin=None, stdout=fhandle, stderr=fhandle)
        self.leader = phandle
        self.replicas[phandle] = fhandle
        self.output("Leader restarted.")
        
    def _kill_an_acceptor(self):
        for phandle, fhandle in self.acceptors.iteritems():
            phandle.terminate()
            fhandle.close()
            del self.acceptors[phandle]

    def _kill_a_replica(self):
        for phandle, fhandle in self.replicas.iteritems():
            phandle.terminate()
            fhandle.close()
            del self.replicas[phandle]

    def _kill_a_coordinator(self):
        for phandle, fhandle in self.coordinators.iteritems():
            phandle.terminate()
            fhandle.close()
            del self.coordinators[phandle]

    def _kill_a_client(self):
        for phandle, fhandle in self.clients.iteritems():
            phandle.terminate()
            fhandle.close()
            del self.clients[phandle]

    def _kill_all(self):
        phandles = self.clients.keys() + self.acceptors.keys() + self.coordinators.keys() + self.replicas.keys()
        fhandles = self.replicas.values() + self.acceptors.values() + self.clients.values() + self.coordinators.values()
        for phandle in phandles:
            phandle.terminate()
        self.output("All processes killed.")
        for fhandle in fhandles:
            fhandle.close()
        self.output("All files closed.")        
        self.clients = self.acceptors = self.replicas = self.coordinators ={}
        subprocess.call(['rm', '-rf', 'ports'])
        
    def output(self, text):
        print "[Test] %s" % text
    
def main():
    tester = SanityChecker(numreplicas=options.numreplicas, numcoords=options.numcoords, numacceptors=options.numacceptors, numclients=options.numclients, clientinput=options.clientinput)
    tester.output("Starting Test 1...")
    tester.test1()
    sleep(1)
    tester.test1_check()
#    tester.output("Starting Test 2...")
#    tester.test2()
#    tester.test2_check()
#    sleep(1)
#    tester.output("Starting Test 3...")
#    tester.test3()
#    tester.test3_check()
    
if __name__=='__main__':
    main()
