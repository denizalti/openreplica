import time
import cPickle
import sys
from pvalue import *
from concoord.pack import *

def pick(a):
    cPickle.dumps(a)

def st(a):
    str(a)

def measure(method, a):
    s = time.time()
    method(a)
    return time.time()-s

x = time.time()
p = PValue((1,'1.2.3.4:14000'),6787687538753,('1,2,3,4,4,4,4,,4,4', 2578358375837538753, ('test',2,3,4)))
print "NamedTuple creation time:", time.time()-x

x = time.time()
r = PValueOld((1,'1.2.3.4:14000'),6787687538753,('1,2,3,4,4,4,4,,4,4', 2578358375837538753, ('test',2,3,4)))
print "Object creation time:", time.time()-x

print "Length of namedtuple: ", sys.getsizeof(p)
print "Length of object: ", sys.getsizeof(r)

pt = []
rt = []

for i in xrange(1000):
    pt.append(p)
    rt.append(r)

print "Length of pickled namedtuple:", len(cPickle.dumps(pt))
print "Length of stred namedtuple:", len(str(pt))

print "Pickling namedtuple:", measure(pick, pt)
print "Pickling object:",measure(pick, rt)

print "String namedtuple:",measure(st, pt)
print "String object:",measure(st, rt)
