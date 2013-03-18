import time
from concoord.pack import *

dict = {}
dict[1] = (1, '1.2.3.4:14000')
dict[2] = 6787687538753
dict[3] = ('1,2,3,4,4,4,4,,4,4', 2578358375837538753, ('test',2,3,4))

msg = PValue((1,'1.2.3.4:14000'),
             6787687538753,
             ('1,2,3,4,4,4,4,,4,4', 2578358375837538753, ('test',2,3,4)))

s = time.time()
Peer(*dict[3])
print "Time spent: ", time.time()-s

s = time.time()
Peer(dict[3][0], dict[3][1], dict[3][2])
print "Time spent: ", time.time()-s

