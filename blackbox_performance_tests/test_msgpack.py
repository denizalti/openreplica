import time
from concoord.pack import *
import msgpack
from threading import Lock
from concoord.enums import *

MSGID = 0
MSGTYPE = 1
MSGSRC = 2
BALLOTNUMBER = 3
COMMANDNUMBER = 4
PROPOSAL = 5
DECISIONS = 6
REPLY = 7
REPLYCODE = 8
INRESPONSETO = 9
SNAPSHOT = 10

msgidpool = 0
msgidpool_lock = Lock() 

def assignuniqueid():
    global msgidpool
    global msgidpool_lock
    with msgidpool_lock:
        tempid = msgidpool
        msgidpool += 1
    return tempid

def create_msg(type, src, *args):
    m = {}
    m[MSGID] = assignuniqueid()
    m[MSGTYPE] = type
    m[MSGSRC] = src
    for type,obj in args:
        m[type] = obj
    return m

def parse_msg(msg):
    src = Peer(*msg[MSGSRC])
    if msg[MSGTYPE] == MSG_HELO or msg[MSGTYPE] == MSG_PING or  msg[MSGTYPE] == MSG_BYE or  msg[MSGTYPE] == MSG_UPDATE:
        return Message(msg[MSGID], msg[MSGTYPE], src)
    elif msg[MSGTYPE] == MSG_UPDATEREPLY:
        return Message(msg[MSGID], msg[MSGTYPE], src, msg[DECISIONS])

p = create_msg(MSG_HELO, ('1.2.3.4:14000', 14000, 1), (BALLOTNUMBER, (1,'1.2.3.4:14000')), (COMMANDNUMBER,2578358375837538753), (SNAPSHOT, 12345))

s = time.time()
t = msgpack.packb(p)
print "Time spent packing: ", time.time()-s
print "Data length: ", len(t)
s = time.time()
q = msgpack.unpackb(t)
parse_msg(q)
print "Time spent unpacking: ", time.time()-s
