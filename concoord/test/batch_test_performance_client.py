"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Client to test concoord implementation
@copyright: See LICENSE
"""
import argparse
import os, sys
import time
from batch_test_performance_proxy import Test

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
  try:
    for i in range(args.operations/10):
      reqdesc = proxy.getvalue()
    starttime = time.time()
    for i in range(args.operations):
      reqdesc = proxy.getvalue()
    reqdesc.finalize()
    stoptime = time.time()

    with reqdesc.replyarrivedcond:
      while not reqdesc.replyarrived:
        reqdesc.replyarrivedcond.wait()
  except KeyboardInterrupt:
    print "Exiting.."
    _exit()

  throughput = 1.0/(float(stoptime-starttime)/(args.operations+1))
  print "*****************************************"
  print "AVERAGE THROUGHPUT: {:,} ops/sec".format(throughput)
  if args.setting:
    r,a = args.setting.split(',')
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
