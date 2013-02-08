from concoord.pack import *
from concoord.enums import *
from concoord.pvalue import *
import msgpack
from threading import Lock

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
PVALUESET = 11
LEADER = 12

msgidpool = 0
msgidpool_lock = Lock()

def assignuniqueid():
    global msgidpool
    global msgidpool_lock
    with msgidpool_lock:
        tempid = msgidpool
        msgidpool += 1
    return tempid

def create_message(type, src, *args):
    m = {}
    m[MSGID] = assignuniqueid()
    m[MSGTYPE] = type
    m[MSGSRC] = src
    for type,obj in args:
        m[type] = obj
    return m

def parse_message(msg):
    src = Peer(*msg[MSGSRC])
    if msg[MSGTYPE] == MSG_HELO or msg[MSGTYPE] == MSG_PING or  msg[MSGTYPE] == MSG_BYE or msg[MSGTYPE] == MSG_UPDATE:
        return Message(msg[MSGID], msg[MSGTYPE], src)
    elif msg[MSGTYPE] == MSG_UPDATEREPLY:
        return UpdateReplyMessage(msg[MSGID], msg[MSGTYPE], src, msg[DECISIONS])
    elif msg[MSGTYPE] == MSG_PREPARE:
        return PrepareMessage(msg[MSGID], msg[MSGTYPE], src, msg[BALLOTNUMBER])
    elif msg[MSGTYPE] == MSG_PREPARE_ADOPTED or msg[MSGTYPE] == MSG_PREPARE_PREEMPTED:
        pvalueset = PValueSet()
        pvalueset.pvalues = msg[PVALUESET]
        return PrepareReplyMessage(msg[MSGID], msg[MSGTYPE], src,
                                   msg[BALLOTNUMBER], msg[INRESPONSETO],
                                   pvalueset)
    elif msg[MSGTYPE] == MSG_PROPOSE:
        proposal = Proposal(*msg[PROPOSAL])
        print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        print msg
        print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        return ProposeMessage(msg[MSGID], msg[MSGTYPE], src,
                              msg[BALLOTNUMBER], msg[COMMANDNUMBER],
                              proposal)
    elif msg[MSGTYPE] == MSG_PROPOSE_ACCEPT or msg[MSGTYPE] == MSG_PROPOSE_REJECT:
        return ProposeReplyMessage(msg[MSGID], msg[MSGTYPE], src)
    elif msg[MSGTYPE] == MSG_PERFORM:
        return Message(msg[MSGID], msg[MSGTYPE], src)
    elif msg[MSGTYPE] == MSG_RESPONSE:
        return Message(msg[MSGID], msg[MSGTYPE], src)
    elif msg[MSGTYPE] == MSG_CLIENTREQUEST:
        return Message(msg[MSGID], msg[MSGTYPE], src)
    elif msg[MSGTYPE] == MSG_CLIENTREPLY:
        return Message(msg[MSGID], msg[MSGTYPE], src)
    elif msg[MSGTYPE] == MSG_INCCLIENTREQUEST:
        return Message(msg[MSGID], msg[MSGTYPE], src)
    elif msg[MSGTYPE] == MSG_GARBAGECOLLECT:
        return Message(msg[MSGID], msg[MSGTYPE], src, msg[COMMANDNUMBER], msg[SNAPSHOT])
    elif msg[MSGTYPE] == MSG_STATUS:
        return Message(msg[MSGID], msg[MSGTYPE], src)
