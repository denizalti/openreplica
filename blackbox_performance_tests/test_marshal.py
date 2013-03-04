import time
from concoord.pack import *
from concoord.pvalue import *
import marshal

p = PValue((1,'1.2.3.4:14000'),6787687538753,('1,2,3,4,4,4,4,,4,4', 2578358375837538753, ('test',2,3,4)))
p = PValueSet()
p = "KEMAL", 7897897
s = time.time()
t = marshal.dumps(p)
print "Time spent: ", time.time()-s
print "Data length: ", len(t)
q = marshal.loads(t)
print q
print type(q)
