import time
from concoord.pack import *
from types import *
import struct

def handle_types(msg):
    packfmt = ''
    for thing in msg:
        if type(thing) == IntType:
            if thing <= 4294967295:
                packfmt += 'I'
            else:
                packfmt += 'L'
        elif type(thing) == StringType:
            packfmt += '%ds' % len(thing)
        elif type(thing) == TupleType:
            packfmt += handle_types(thing)

    return packfmt

msg = PValue((1,'1.2.3.4:14000'),6787687538753,('1,2,3,4,4,4,4,,4,4', 2578358375837538753, ('test',2,3,4)))
s = time.time()
packfmt = handle_types(msg)
print packfmt
t = struct.pack(packfmt, msg[0][0], msg[0][1], msg[1], msg[2][0], msg[2][1], msg[2][2][0], msg[2][2][1], msg[2][2][2], msg[2][2][3])
print "Time spent: ", time.time()-s
print "Data length: ", len(t)
q = struct.unpack(packfmt, t)
print q

