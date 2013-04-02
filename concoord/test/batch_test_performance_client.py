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
from batch_test_performance_proxy import *
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
  for i in range(options.operations/10):
    reqdesc = proxy.getvalue()
  starttime = time.time()
  for i in range(options.operations):
    reqdesc = proxy.getvalue()
  stoptime = time.time()

  with reqdesc.replyarrivedcond:
    while not reqdesc.replyarrived:
      reqdesc.replyarrivedcond.wait()

  latency = float(stoptime-starttime)/(options.operations+1)
  print "*****************************************"
  print "AVERAGE CLIENT LATENCY: %.10f secs" % latency 
  if options.setting:
    r,a = options.setting.split(',')
    print " for %s Replicas %s Acceptors." % (r,a)
  print "*****************************************"
  sys.stdout.flush()
  sys.stderr.flush()
  os._exit(0)

def main():
  test_loop()
    
if __name__=='__main__':
  main()
