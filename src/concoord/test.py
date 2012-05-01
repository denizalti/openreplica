import socket, os, sys, time, random, threading, time
from concoord.proxy.bank import Bank

b = Bank(sys.argv[1], multi=True)
b.open("deniz")
b.deposit("deniz", 0)
b.deposit("deniz", 0)
b.deposit("deniz", 0)
b.deposit("deniz", 0)
b.deposit("deniz", 0)
start = time.time()
for i in range(1000):
    b.deposit("deniz", 0)
now = time.time()

print "TOTAL TIME: ", now-start
