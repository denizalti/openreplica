# Create 5 replicas and kill them in turn, until 1 is left
# Every time kill the leader
# Then bring the leaders back in the reverse order, forcing 4 handovers.
import signal, time
import subprocess
import time
from concoord.proxy.counter import Counter

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

@timeout(120)
def test_failure(numreplicas):
    replicas = []
    acceptors = []
    replicanames = []

    print "Running replica 0"
    replicas.append(subprocess.Popen(['concoord', 'replica',
                                      '-o', 'concoord.object.counter.Counter',
                                      '-a', '127.0.0.1', '-p', '14000']))
    replicanames.append("127.0.0.1:14000")

    for i in range(3):
        print "Running acceptor %d" %i
        acceptors.append(subprocess.Popen(['concoord', 'acceptor', '-b', '127.0.0.1:14000']))

    for i in range(1, numreplicas):
        print "Running replica %d" %i
        replicas.append(subprocess.Popen(['concoord', 'replica',
                                      '-o', 'concoord.object.counter.Counter',
                                      '-a', '127.0.0.1', '-p', '1400%d'%i,
                                      '-b', '127.0.0.1:14000']))
        replicanames.append("127.0.0.1:1400%d"%i)

    # Give the system sometime to initialize
    time.sleep(10)

    replicastring = ','.join(replicanames)
    # Test Clientproxy operations
    c = Counter(replicastring)
    for i in range(50):
        c.increment()
    print "Counter value after 50 increments: %d" % c.getvalue()

    # Start kiling replicas
    print "Killing replicas one by one."
    for i in range(numreplicas-1):
        print "Killing replica %d" %i
        replicas[i].kill()

        # Clientproxy operations should still work
        c = Counter('127.0.0.1:1400%d'%(i+1))
        for i in range(50):
            c.increment()
        print "Counter value after 50 more increments: %d" % c.getvalue()

    # Start bringing replicas back
    for i in reversed(xrange(numreplicas-1)):
        print "Running replica %d" %i
        replicas.append(subprocess.Popen(['concoord', 'replica',
                                      '-o', 'concoord.object.counter.Counter',
                                      '-a', '127.0.0.1', '-p', '1400%d'%i,
                                      '-b', '127.0.0.1:1400%d' %(i+1)]))
        time.sleep(10)
        # Clientproxy operations should still work
        connected = False
        while(not connected):
            try:
                c = Counter('127.0.0.1:1400%d'%i)
            except:
                continue
            connected = True

        for i in range(50):
            c.increment()
        print "Counter value after 50 more increments: %d" % c.getvalue()

    for p in (replicas+acceptors):
        p.kill()
    return True

def main():
    print "===== TEST 5 REPLICAS ====="
    s = "PASSED" if test_failure(5) else "TIMED OUT"
    print "===== TEST %s =====" % s

if __name__ == '__main__':
    main()
