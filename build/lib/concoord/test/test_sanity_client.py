"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Client to test concoord implementation
@copyright: See LICENSE
"""
import argparse
import random
import os, sys
import threading
from threading import Lock, Thread
from test_sanity_proxy import *

parser = argparse.ArgumentParser()

parser.add_argument("-b", "--boot", action="store", dest="bootstrap",
                    help="address:port tuple for the bootstrap peer")
args = parser.parse_args()

shared_local_history = {}
shared_local_history_lock = Lock()
 
def start_test():
  thread_one = Thread(target=test_loop, name='C1')
  thread_two = Thread(target=test_loop, name='C2')
  thread_one.start()
  thread_two.start()

def test_loop():
  proxy = Value(args.bootstrap)
  while True:
    op = random.randint(1,2)%2
    if op == 0:
      op_num = proxy.add_10_percent()
      if op_num:
        with shared_local_history_lock:
          shared_local_history[op_num] = op
    else:
      op_num = proxy.subtract_10000()
      if op_num:
        with shared_local_history_lock:
          shared_local_history[op_num] = op
  
    if len(shared_local_history) % 2000 == 0:
      print threading.current_thread().name, ": CHECK POINT"
      # Compare it with remote state
      remote_value, remote_counter = proxy.get_data()
      # Execute the history locally
      value = 10**6
      # Go through the history in op_num order
      for i in range(remote_counter):
        try:
          if shared_local_history[i+1] == 0:
            value *= 1.1
          else:
            value -= 10**4
        except KeyError:
          continue

      if remote_value != value:
        print "ERROR: The remote state does not match the local state."
        print "REMOTE STATE VALUE: %d" % remote_value
        print "LOCAL  STATE VALUE: %d" % value
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)

def main():
  start_test()
    
if __name__=='__main__':
    main()
