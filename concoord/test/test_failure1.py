# Create two acceptors then kill the first one
import subprocess
import time
from concoord.proxy.counter import Counter

def main():
    print ("Running replica 0")
    replica0  = subprocess.Popen(['concoord', 'replica', '-o', 'concoord.object.counter.Counter',
                               '-a', '127.0.0.1', '-p', '14000']); replica0
    print ("Running acceptor 0")
    acceptor0 = subprocess.Popen(['concoord', 'acceptor', '-b', '127.0.0.1:14000'])

    time.sleep(3)

    print ("Running acceptor1 ")
    acceptor1 = subprocess.Popen(['concoord', 'acceptor', '-b', '127.0.0.1:14000']); acceptor1

    time.sleep(3)

    print ("Running acceptor2 ")
    acceptor2 = subprocess.Popen(['concoord', 'acceptor', '-b', '127.0.0.1:14000']); acceptor2

    time.sleep(3)

    # Now kill acceptor0, and system does not work
    print ("Killing acceptor 0")
    acceptor0.kill()

    # Now client/proxy operations still work
    c = Counter("127.0.0.1:14000, 127.0.0.1:14001, 127.0.0.1:14002", debug = True)
    for i in range(1000):
        c.increment()
    print "The value after 1000 increments:", c.getvalue()

    # Clean up
    acceptor1.kill()
    acceptor2.kill()
    replica0.kill()

if __name__ == '__main__':
    main()
