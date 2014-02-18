# Create two replica-acceptor pairs, then kill the second pair
from __future__ import print_function
import subprocess
import time
from concoord.proxy.counter import Counter

def main():
    print ("Running replica 0")
    replica0  = subprocess.Popen(['concoord', 'replica', '-o', 'concoord.object.counter.Counter',
                               '-a', '127.0.0.1', '-p', '14000']); replica0

    print ("Running acceptor 0")
    acceptor0 = subprocess.Popen(['concoord', 'acceptor', '-b', '127.0.0.1:14000']);acceptor0

    time.sleep(3)

    c = Counter("127.0.0.1:14000, 127.0.0.1:14001, 127.0.0.1:14002", debug = True)
    print ("increment of counter returned", c.increment())
    print ("getvalue of counter returned", c.getvalue())

    time.sleep(1)

    print ("Running replica 1") # concoord replica -o concoord.object.counter.Counter -b 127.0.0.1:14000 -a 127.0.0.1 -p 14001
    replica1  = subprocess.Popen(['concoord', 'replica', '-o', 'concoord.object.counter.Counter', '-b', '127.0.0.1:14000',
                               '-a', '127.0.0.1', '-p', '14001']); replica1
    time.sleep(1)

    print ("Running acceptor 1 ")
    acceptor1 = subprocess.Popen(['concoord', 'acceptor', '-b', '127.0.0.1:14000']); acceptor1
    time.sleep(1)

    print ("Running acceptor 2 ")
    acceptor2 = subprocess.Popen(['concoord', 'acceptor', '-b', '127.0.0.1:14000']); acceptor2
    time.sleep(1)

    # Now kill acceptor0, and system does not work
    print ("Killing replica 1")
    replica1.kill()
    time.sleep(1)
    print ("Killing acceptor 1")
    acceptor1.kill()
    time.sleep(1)

    # Now client/proxy operations still work
    print ("increment of counter returned", c.increment())
    print ("getvalue of counter returned", c.getvalue())

    # Clean up
    replica0.kill()
    acceptor0.kill()
    acceptor2.kill()

    print ("All done,quiting.")
if __name__ == '__main__':
    main()
