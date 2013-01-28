"""
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Client to test concoord implementation
@copyright: See LICENSE
"""
import random
import os, sys
import threading
from threading import Lock, Thread
from _test_proxy import *
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-b", "--boot", action="store", dest="bootstrap",
                  help="address:port:type triple for the bootstrap peer")
(options, args) = parser.parse_args()

def test_loop():
  proxy = Test(options.bootstrap)
  for i in range(100000):
    op = random.randint(1,2)%2
    if op == 0:
      proxy.getvalue()
    else:
      proxy.setvalue(10000)
  
  sys.stdout.flush()
  sys.stderr.flush()
  os._exit(0)

def main():
  test_loop()
    
if __name__=='__main__':
    main()
