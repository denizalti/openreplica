# Create two replicas and two acceptors
# kill the first two, and then recreate them connecting to the new ones.
# Value returned from second increment is wrong. (1 is the supported number for 2*1+1=3 according to section 4.6 of the paper.
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
    print ("Running acceptor 1")
    acceptor1 = subprocess.Popen(['concoord', 'acceptor', '-b', '127.0.0.1:14000']); acceptor1
    time.sleep(1)

    print ("Running replica 2") # concoord replica -o concoord.object.counter.Counter -b 127.0.0.1:14000 -a 127.0.0.1 -p 14001
    replica2  = subprocess.Popen(['concoord', 'replica', '-o', 'concoord.object.counter.Counter', '-b', '127.0.0.1:14000',
                               '-a', '127.0.0.1', '-p', '14002']); replica2
    print ("Running acceptor 2")
    acceptor2 = subprocess.Popen(['concoord', 'acceptor', '-b', '127.0.0.1:14000']); acceptor2
    time.sleep(1)

    print ("Killing replica 0")
    replica0.kill()
    time.sleep(1)
    print ("Killing acceptor 0")
    acceptor0.kill()
    time.sleep(11)

    # Now create another replica and acceptor, connecting to the new leader
    print ("Running replica 0 once again")
    new_replica0  = subprocess.Popen(['concoord', 'replica', '-o', 'concoord.object.counter.Counter', '-b', '127.0.0.1:14001',
                               '-a', '127.0.0.1', '-p', '14000']); new_replica0
    print ("Running acceptor 3")
    acceptor3 = subprocess.Popen(['concoord', 'acceptor', '-b', '127.0.0.1:14001']); acceptor3

    print ("increment of counter returned", c.increment())
    value_after_2_incs = c.getvalue()
    print ("getvalue of counter returned", c.getvalue())
    assert value_after_2_incs == 2, "Counter object returned wrong value after two increments: %r" %(value_after_2_incs,)

    # Clean up
    replica0.kill()
    replica1.kill()
    replica2.kill()
    new_replica0.kill()
    acceptor0.kill()
    acceptor1.kill()
    acceptor2.kill()
    acceptor3.kill()

    print ("All done,quiting.")
if __name__ == '__main__':
    main()
