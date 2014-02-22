# Create 3,5 and 7 Acceptors, kill the minority at once
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

@timeout(60)
def test_failure(numacceptors):
    acceptors = []

    print "Running replica 0"
    replica = subprocess.Popen(['concoord', 'replica',
                                '-o', 'concoord.object.counter.Counter',
                                '-a', '127.0.0.1', '-p', '14000'])
    for i in range(numacceptors):
        print "Running acceptor %d" %i
        acceptors.append(subprocess.Popen(['concoord', 'acceptor', '-b', '127.0.0.1:14000']))

    # Give system time to stabilize
    time.sleep(10)

    c = Counter("127.0.0.1:14000", debug = True)
    for i in range(100):
        c.increment()
    print "Counter value after 100 increments: %d" % c.getvalue()

    for i in range((numacceptors-1)/2):
        print "Killing acceptor %d" %i
        acceptors[i].kill()

    for i in range(100):
        c.increment()
    print "Counter value after 100 more increments: %d" % c.getvalue()

    replica.kill()
    for a in (acceptors):
        a.kill()
    return True

def main():
    print "===== TEST 3 ACCEPTORS ====="
    s = "PASSED" if test_failure(3) else "TIMED OUT"
    print "===== TEST %s =====" % s
    print "===== TEST 5 ACCEPTORS ====="
    s = "PASSED" if test_failure(5) else "TIMED OUT"
    print "===== TEST %s =====" % s
    print "===== TEST 7 ACCEPTORS ====="
    s = "PASSED" if test_failure(7) else "TIMED OUT"
    print "===== TEST %s =====" % s

if __name__ == '__main__':
    main()
