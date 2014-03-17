# Creates a partition and tests ConCoord's behavior.
# Create 3 replicas
# Create 2 partitions P1 and P2 as follows:
# P1: 1 Replica: Minority
# P2: 2 Replicas: Majority
# Since P2 has majority of the replicas, P2 should make progress
import sys, os
import signal, time
import socket, struct
import cPickle as pickle
import subprocess
from concoord.message import *
from concoord.proxy.counter import Counter
from concoord.exception import ConnectionError

class TimeoutException(Exception):
    pass

def get_replica_status(replica):
    # Create Status Message
    sm = create_message(MSG_STATUS, None)
    messagestr = msgpack.packb(sm)
    message = struct.pack("I", len(messagestr)) + messagestr

    addr, port = replica.split(':')
    try:
        # Open a socket
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        s.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        s.settimeout(22)
        s.connect((addr,int(port)))
        s.send(message)
        lstr = s.recv(4)
        msg_length = struct.unpack("I", lstr[0:4])[0]
        msg = ''
        while len(msg) < msg_length:
            chunk = s.recv(msg_length-len(msg))
            msg = msg + chunk
            if chunk == '':
                break
        s.close()
        return pickle.loads(msg)
    except:
        print "Cannot connect to Replica  %s:%d" % (addr, int(port))
        return None

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
    for i in range(50):
        c_minority.increment()
    # This method will timeout before it reaches here.
    print "Counter value: %d" % c_minority.getvalue()
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

    # P2 Nodes
    print "Running replica 1"
    p = subprocess.Popen(['concoord', 'replica',
                          '-o', 'concoord.object.counter.Counter',
                          '-a', '127.0.0.1', '-p', '14001',
                          '-b', '127.0.0.1:14000'])
    processes.append(p)
    p2_pids.append(p.pid)

    print "Running replica 2"
    p = subprocess.Popen(['concoord', 'replica',
                          '-o', 'concoord.object.counter.Counter',
                          '-a', '127.0.0.1', '-p', '14002',
                          '-b', '127.0.0.1:14000'])
    processes.append(p)
    p2_pids.append(p.pid)

    # Give the system some time to initialize
    time.sleep(10)

    # This client can only connect to the replicas in this partition
    c_P1 = Counter('127.0.0.1:14000')
    c_P2 = Counter('127.0.0.1:14001,127.0.0.1:14002')
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
    p1_ports = [14000]
    p2_ports = [14001, 14002]
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

    for porttoblock in p2_ports:
        iptablerules.append(subprocess.Popen(['sudo', 'iptables',
                                              '-I', 'INPUT',
                                              '-p', 'tcp',
                                              '--dport', '%d'%porttoblock,
                                              '--sport', '14000',
                                              '-j', 'DROP']))

    print "Created the partition. Waiting for system to stabilize."
    time.sleep(20)

    # c_P2 should make progress
    print "Connecting to the majority, which should have a new leader."
    for i in range(50):
        c_P2.increment()
    print "Counter value after 50 more increments: %d" % c_P2.getvalue()
    if c_P2.getvalue() == 100:
        print "SUCCESS: Majority made progress."

    print "Connecting to the minority, which should not make progress."
    if connect_to_minority():
        print "===== TEST FAILED ====="
        sys.exit('Minority made progress.')
    print "SUCCESS: Minority did not make progress."

    print "Ending partition."
    # End partition
    with open('test.iptables.rules', 'r') as input:
        subprocess.Popen(['sudo', 'iptables-restore'], stdin=input)
    subprocess.Popen(['sudo', 'rm', 'test.iptables.rules'])

    time.sleep(40)
    # c_P1 should make progress
    print "Connecting to the old leader."
    if not connect_to_minority():
        print "===== TEST FAILED ====="
        print "Old leader could not recover after partition."
        print get_replica_status('127.0.0.1:14000')
        for p in (processes):
            p.kill()
        return True
    if c_P1.getvalue() == 150:
        print "SUCCESS: Old leader recovered."
        print "===== TEST PASSED ====="
    else:
        print "FAILURE: Old leader lost some client commands."
        print "===== TEST FAILED ====="
    print get_replica_status('127.0.0.1:14000')

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
