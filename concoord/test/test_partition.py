# Creates a partition and tests ConCoords behavior.
# Create 3 replicas and 3 acceptors
# Create 2 partitions P1 and P2 as follows:
# P1: 2 Replicas 1 Acceptor : Minority
# P2: 1 Replica 2 Acceptors : Majority
# Since P2 has majority of the acceptors, P2 should make progress

import signal, time
import subprocess
import time
from concoord.proxy.counter import Counter
from concoord.exception import ConnectionError

class TimeoutException(Exception):
    pass

def timeout(timeout):
    def timeout_function(f):
        def f2(*args):
            def timeout_handler(signum, frame):
                raise TimeoutException()

            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout) # trigger alarm in timeout seconds
            try:
                retval = f(*args)
            except TimeoutException:
                return False
            finally:
                signal.signal(signal.SIGALRM, old_handler)
            signal.alarm(0)
            return retval
        return f2
    return timeout_function

@timeout(30)
def connect_to_minority():
    c_minority = Counter('127.0.0.1:14000')
    print "Connecting to minority"
    for i in range(10):
        c_minority.increment()
    # This method will timeout before it reaches here.
    print "P2 Client Made Progress: Counter value: %d" % c_minority.getvalue()
    return True

def test_partition():
    # get ip
    # subprocess.check_output("/sbin/ifconfig eth0 | awk '/inet/ { print $2 } ' | sed -e s/addr://", shell=True).split()[0]

    numreplicas = 3
    numacceptors = 3
    replicas = []
    acceptors = []

    print "Running replica 0"
    replicas.append(subprocess.Popen(['concoord', 'replica',
                                      '-o', 'concoord.object.counter.Counter',
                                      '-a', '127.0.0.1', '-p', '14000', '-d']))

    print "Running replica 1"
    replicas.append(subprocess.Popen(['concoord', 'replica',
                                      '-o', 'concoord.object.counter.Counter',
                                      '-a', '127.0.0.1', '-p', '14001',
                                      '-b', '127.0.0.1:14000', '-d']))

    print "Running acceptor 0"
    acceptors.append(subprocess.Popen(['concoord', 'acceptor',
                                       '-a', '127.0.0.1', '-p', '15000',
                                       '-b', '127.0.0.1:14000']))

    print "Running replica 2"
    replicas.append(subprocess.Popen(['concoord', 'replica',
                                      '-o', 'concoord.object.counter.Counter',
                                      '-a', '127.0.0.1', '-p', '14002',
                                      '-b', '127.0.0.1:14000']))

    print "Running acceptor 1"
    acceptors.append(subprocess.Popen(['concoord', 'acceptor',
                                       '-a', '127.0.0.1', '-p', '15001',
                                       '-b', '127.0.0.1:14000']))

    print "Running acceptor 2"
    acceptors.append(subprocess.Popen(['concoord', 'acceptor',
                                       '-a', '127.0.0.1', '-p', '15002',
                                       '-b', '127.0.0.1:14000']))

    # Give the system sometime to initialize
    time.sleep(10)

    # This client can only connect to the replicas in this partition
    c_P1 = Counter('127.0.0.1:14000', debug = True)
    c_P2 = Counter('127.0.0.1:14001, 127.0.0.1:14002')
    # The client should work
    print "Sending requests to the leader"
    for i in range(10):
        c_P1.increment()
    print "Counter value: %d" % c_P1.getvalue()

    # Save iptables settings for later recovery
    #subprocess.Popen(['sudo', 'iptables-save', '>', 'test.iptables.rules'])

    # Start partition
    iptablerules = []
    p1_ports = [14000, 14001, 15000]
    p2_ports = [14002, 15001, 15002]

    # Block all incoming traffic to leader
    iptablerules.append(subprocess.Popen(['sudo', 'iptables',
                                          '-I', 'INPUT',
                                          '-p', 'tcp',
                                          '--dport', '14000',
                                          '-j', 'DROP']))

    print "Created the partition. Waiting for system to stabilize."
    time.sleep(30)
    
    # c_P2 should make progress
    print "Connecting to the majority, which should have a new leader."
    for i in range(10):
        c_P2.increment()
    print "Counter value after 10 increments: %d" % c_P2.getvalue()

    print "Connecting to the minority, which should not make progress."
    if not connect_to_minority():
        print "===== TEST PASSED ====="
    else:
        print "===== TEST FAILED ====="

    print "Ending partition and cleaning up."
    # End partition
    subprocess.Popen(['sudo', 'iptables-restore', '<', 'test.iptables.rules'])
    subprocess.Popen(['sudo', 'rm', 'test.iptables.rules'])


    for p in (replicas+acceptors):
        p.kill()
    return True

def main():
    test_partition()

if __name__ == '__main__':
    main()
