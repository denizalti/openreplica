"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Client to test concoord implementation
@copyright: See LICENSE
"""
import argparse
import os, sys
import time
from test_membership_performance_proxy import *

parser = argparse.ArgumentParser()

parser.add_argument("-b", "--boot", action="store", dest="bootstrap",
                    help="address:port tuple for the bootstrap peer")
parser.add_argument("-n", "--num", action="store", dest="setting",
                    help="x,y tuple for the number of replicas and acceptors")
parser.add_argument("-o", "--op", action="store", dest="operations", type=int,
                    default=10000, help="number of operations")
args = parser.parse_args()

def test_loop():
  proxy = Test(args.bootstrap)
  for i in range(args.operations/10):
    proxy.add("127.0.0.1:14000")
  starttime = time.time()
  for i in range(args.operations):
    proxy.add("127.0.0.1:14000")
  stoptime = time.time()
  latency = float(stoptime-starttime)/(args.operations)
  print "*****************************************"
  print "AVERAGE CLIENT LATENCY: %f secs" % latency
  if args.setting:
    r,a = args.setting.split(',')
    print " for %s Replicas %s Acceptors." % (r,a)
  print "*****************************************"
  sys.stdout.flush()
  sys.stderr.flush()
  os._exit(0)

def main():
  test_loop()

if __name__=='__main__':
    main()
