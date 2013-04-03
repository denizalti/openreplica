"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Client to test concoord implementation
@copyright: See LICENSE
"""
import random
import os, sys
import threading
import time
from threading import Lock, Thread
from async_test_performance_proxy import *
from optparse import OptionParser

parser = OptionParser()

parser.add_option("-b", "--boot", action="store", dest="bootstrap",
                  help="address:port:type triple for the bootstrap peer")
parser.add_option("-n", "--num", action="store", dest="setting",
                  help="x,y tuple for the number of replicas and acceptors")
parser.add_option("-o", "--op", action="store", dest="operations", type='int',
                  default=10000, help="number of operations")

(options, args) = parser.parse_args()

def test_loop():
  proxy = Test(options.bootstrap)
  try:
    for i in range(options.operations/10):
      proxy.getvalue()
    starttime = time.time()
    for i in range(options.operations):
      proxy.getvalue()
    stoptime = time.time()

    reqdesc = proxy.getvalue()
    with reqdesc.replyarrivedcond:
      while not reqdesc.replyarrived:
        reqdesc.replyarrivedcond.wait()
  except KeyboardInterrupt:
    print "Exiting.."
    _exit()

  throughput = 1.0/(float(stoptime-starttime)/(options.operations+1))
  print "*****************************************"
  print "AVERAGE THROUGHPUT: {:,} ops/sec".format(throughput)
  if options.setting:
    r,a = options.setting.split(',')
    print " for %s Replicas %s Acceptors." % (r,a)
  print "*****************************************"
  _exit()

def _exit():
  sys.stdout.flush()
  sys.stderr.flush()
  os._exit(0)

def main():
  test_loop()
    
if __name__=='__main__':
  main()
