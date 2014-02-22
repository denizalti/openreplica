# Cuts the connection to the leader and tests liveness

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
def connect_to_leader():
    c_leader = Counter('127.0.0.1:14000')
    print "Connecting to old leader"
    for i in range(100):
        c_leader.increment()
    # This method will timeout before it reaches here.
    print "Client Made Progress: Counter value: %d" % c_minority.getvalue()
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
                                      '-a', '127.0.0.1', '-p', '14000']))

    print "Running replica 1"
    replicas.append(subprocess.Popen(['concoord', 'replica',
                                      '-o', 'concoord.object.counter.Counter',
                                      '-a', '127.0.0.1', '-p', '14001',
                                      '-b', '127.0.0.1:14000']))

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

    # Give the system some time to initialize
    time.sleep(10)

    # This client can only connect to the replicas in this partition
    c_P1 = Counter('127.0.0.1:14000', debug = True)
    c_P2 = Counter('127.0.0.1:14001, 127.0.0.1:14002')
    # The client should work
    print "Sending requests to the leader"
    for i in range(100):
        c_P1.increment()
    print "Counter value after 100 increments: %d" % c_P1.getvalue()

    # Save iptables settings for later recovery
    with open('test.iptables.rules', 'w') as output:
        subprocess.Popen(['sudo', 'iptables-save'], stdout=output)

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

    print "Cutting the connections to the leader. Waiting for system to stabilize."
    time.sleep(10)
    
    print "Connecting to old leader, which should not make progress."
    if connect_to_leader():
        print "===== TEST FAILED ====="
    else:
        # c_P2 should make progress
        print "Connecting to other nodes, which should have a new leader."
        for i in range(100):
            c_P2.increment()
        print "Counter value after 100 increments: %d" % c_P2.getvalue()
        print "===== TEST PASSED ====="

    print "Fixing the connections and cleaning up."
    with open('test.iptables.rules', 'r') as input:
        subprocess.Popen(['sudo', 'iptables-restore'], stdin=input)
    subprocess.Popen(['sudo', 'rm', 'test.iptables.rules'])

    for p in (replicas+acceptors):
        p.kill()
    return True

def main():
    test_partition()

if __name__ == '__main__':
    main()
