# Cuts the connection to the leader and tests liveness
import sys,os
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

def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None

@timeout(30)
def connect_to_leader():
    c_leader = Counter('127.0.0.1:14000')
    print "Connecting to old leader"
    for i in range(100):
        c_leader.increment()
    # This method will timeout before it reaches here.
    print "Client Made Progress: Counter value: %d" % c_minority.getvalue()
    return True

def test_timeout():
    numreplicas = 3
    numacceptors = 3
    processes = []

    print "Running replica 0"
    processes.append(subprocess.Popen(['concoord', 'replica',
                                      '-o', 'concoord.object.counter.Counter',
                                      '-a', '127.0.0.1', '-p', '14000']))

    for i in range(numacceptors):
        print "Running acceptor %d" %i
        processes.append(subprocess.Popen(['concoord', 'acceptor', '-b', '127.0.0.1:14000']))

    for i in range(1, numreplicas):
        print "Running replica %d" %i
        processes.append(subprocess.Popen(['concoord', 'replica',
                                           '-o', 'concoord.object.counter.Counter',
                                           '-a', '127.0.0.1', '-p', '1400%d'%i,
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

    # Block all incoming traffic to leader
    iptablerule = subprocess.Popen(['sudo', 'iptables',
                                          '-I', 'INPUT',
                                          '-p', 'tcp',
                                          '--dport', '14000',
                                          '-j', 'DROP'])

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

    for p in (processes):
        p.kill()
    return True

def main():
    if not which('iptables'):
        sys.exit('Test requires iptables to run')

    if not os.geteuid() == 0:
        sys.exit('Script must be run as root')

    test_timeout()

if __name__ == '__main__':
    main()
