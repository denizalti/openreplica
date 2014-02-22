# Creates a partition and tests ConCoords behavior.
# Create 2 replicas and 3 acceptors
# Create 2 partitions P1 and P2 as follows:
# P1: 1 Replica 1 Acceptor : Minority
# P2: 1 Replica 2 Acceptors : Majority
# Since P2 has majority of the acceptors, P2 should make progress
import sys, os
import signal, time
import subprocess
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
def connect_to_minority():
    c_minority = Counter('127.0.0.1:14000')
    print "Connecting to minority"
    for i in range(50):
        c_minority.increment()
    # This method will timeout before it reaches here.
    print "P2 Client Made Progress: Counter value: %d" % c_minority.getvalue()
    return True

def test_partition():
    processes = []
    p1_pids = []
    p2_pids = []

    # P1 Nodes
    print "Running replica 0"
    p = subprocess.Popen(['concoord', 'replica',
                          '-o', 'concoord.object.counter.Counter',
                          '-a', '127.0.0.1', '-p', '14000'])
    processes.append(p)
    p1_pids.append(p.pid)

    print "Running acceptor 0"
    p = subprocess.Popen(['concoord', 'acceptor',
                          '-a', '127.0.0.1', '-p', '15000',
                          '-b', '127.0.0.1:14000'])
    processes.append(p)
    p1_pids.append(p.pid)

    # P2 Nodes
    print "Running replica 1"
    p = subprocess.Popen(['concoord', 'replica',
                          '-o', 'concoord.object.counter.Counter',
                          '-a', '127.0.0.1', '-p', '14001',
                          '-b', '127.0.0.1:14000'])
    processes.append(p)
    p2_pids.append(p.pid)

    print "Running acceptor 1"
    p = subprocess.Popen(['concoord', 'acceptor',
                          '-a', '127.0.0.1', '-p', '15001',
                          '-b', '127.0.0.1:14000'])
    processes.append(p)
    p2_pids.append(p.pid)

    print "Running acceptor 2"
    p = subprocess.Popen(['concoord', 'acceptor',
                          '-a', '127.0.0.1', '-p', '15002',
                          '-b', '127.0.0.1:14000'])
    processes.append(p)
    p2_pids.append(p.pid)

    # Give the system some time to initialize
    time.sleep(10)

    # This client can only connect to the replicas in this partition
    c_P1 = Counter('127.0.0.1:14000', debug = True)
    c_P2 = Counter('127.0.0.1:14001')
    # The client should work
    print "Sending requests to the leader"
    for i in range(50):
        c_P1.increment()
    print "Counter value after 50 increments: %d" % c_P1.getvalue()

    # Save iptables settings for later recovery
    with open('test.iptables.rules', 'w') as output:
        subprocess.Popen(['sudo', 'iptables-save'], stdout=output)

    # Start partition
    iptablerules = []
    p1_ports = [14000, 15000]
    p2_ports = [14001, 15001, 15002]
    connectedports = []

    # Find all ports that R1, A1 and A2 and have connecting to R0 and A0
    for port in p1_ports:
        for pid in p2_pids:
            p1 = subprocess.Popen(['lsof', '-w', '-a', '-p%d'%pid, '-i4'], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(['grep', ':%d'%port], stdin=p1.stdout, stdout=subprocess.PIPE)
            output = p2.communicate()[0]
            if output:
                connectedports.append(output.split()[8].split('->')[0].split(':')[1])

    # Block all traffic to/from R0 and A0 from other nodes but each other
    for porttoblock in connectedports:
        iptablerules.append(subprocess.Popen(['sudo', 'iptables',
                                              '-I', 'INPUT',
                                              '-p', 'tcp',
                                              '--dport', '14000',
                                              '--sport', porttoblock,
                                              '-j', 'DROP']))
        iptablerules.append(subprocess.Popen(['sudo', 'iptables',
                                              '-I', 'INPUT',
                                              '-p', 'tcp',
                                              '--dport', '15000',
                                              '--sport', porttoblock,
                                              '-j', 'DROP']))
    for porttoblock in p2_ports:
        iptablerules.append(subprocess.Popen(['sudo', 'iptables',
                                              '-I', 'INPUT',
                                              '-p', 'tcp',
                                              '--dport', '%d'%porttoblock,
                                              '--sport', '14000',
                                              '-j', 'DROP']))
        iptablerules.append(subprocess.Popen(['sudo', 'iptables',
                                              '-I', 'INPUT',
                                              '-p', 'tcp',
                                              '--dport', '%d'%porttoblock,
                                              '--sport', '15000',
                                              '-j', 'DROP']))

    print "Created the partition. Waiting for system to stabilize."
    time.sleep(20)

    # c_P2 should make progress
    print "Connecting to the majority, which should have a new leader."
    for i in range(50):
        c_P2.increment()
    print "Counter value after 50 more increments: %d" % c_P2.getvalue()

    print "Connecting to the minority, which should not make progress."
    if not connect_to_minority():
        print "===== TEST PASSED ====="
    else:
        print "===== TEST FAILED ====="

    print "Ending partition and cleaning up."
    # End partition
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
        sys.exit('Test must be run as root')

    test_partition()

if __name__ == '__main__':
    main()
