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
from test_performance_proxy import *
from optparse import OptionParser

parser = OptionParser()

parser.add_option("-b", "--boot", action="store", dest="bootstrap",
                  help="address:port:type triple for the bootstrap peer")
parser.add_option("-n", "--num", action="store", dest="setting",
                  help="x,y tuple for the number of replicas and acceptors")
(options, args) = parser.parse_args()

def test_loop():
  proxy = Test(options.bootstrap)
  for i in range(10000):
    if i == 1000:
      starttime = time.time()
    proxy.getvalue()
  
  stoptime = time.time()
  latency = float(stoptime-starttime)/9000
  print "*****************************************"
  print "AVERAGE CLIENT LATENCY: %f secs" % latency 
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
