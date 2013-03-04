import time
from concoord.pack import *
import msgpack
from threading import Lock
from concoord.enums import *
from concoord.message import *

parse_functions = {MSG_HELO: 'parse_basic',
                   MSG_PING: 'parse_basic',
                   MSG_BYE: 'parse_basic',
                   MSG_UPDATE: 'parse_basic',
                   MSG_STATUS: 'parse_basic',
                   MSG_CLIENTREQUEST: 'parse_clientrequest',
                   MSG_CLIENTREPLY: 'parse_clientreply',
                   MSG_PROPOSE: 'parse_propose',
                   MSG_PREPARE: 'parse_prepare',
                   MSG_PROPOSE_ACCEPT: 'parse_propose_reply',
                   MSG_PROPOSE_REJECT: 'parse_propose_reply',
                   MSG_PREPARE_ADOPTED: 'parse_prepare_reply',
                   MSG_PREPARE_PREEMPTED: 'parse_prepare_reply',
                   MSG_PERFORM: 'parse_perform',
                   MSG_RESPONSE: 'parse_response',
                   MSG_INCCLIENTREQUEST: 'parse_incclientrequest',
                   MSG_UPDATEREPLY: 'parse_updatereply',
                   MSG_GARBAGECOLLECT: 'parse_garbagecollect'
                   }

def parse_basic(msg, src):
    return Message(msg[FLD_ID], msg[FLD_TYPE], src)

def parse_clientrequest(msg, src):
    proposalclient = Peer(*msg[FLD_PROPOSAL][0])
    proposal = Proposal(proposalclient, *msg[FLD_PROPOSAL][1:])
    return ClientRequestMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                                proposal, msg[FLD_TOKEN])

def parse_clientreply(msg, src):
    return ClientReplyMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                              msg[FLD_REPLY], msg[FLD_REPLYCODE],
                              msg[FLD_INRESPONSETO])

def parse_msg_func(msg):
    src = Peer(*msg[FLD_SRC])
    return eval(parse_functions[msg[FLD_TYPE]])(msg, src)

def parse_msg_if(msg):
    src = Peer(*msg[FLD_SRC])
    if msg[FLD_TYPE] == MSG_HELO or msg[FLD_TYPE] == MSG_PING or  msg[FLD_TYPE] == MSG_BYE or  msg[FLD_TYPE] == MSG_UPDATE:
        return Message(msg[FLD_ID], msg[FLD_TYPE], src)
    elif msg[FLD_TYPE] == MSG_CLIENTREPLY:
        return ClientReplyMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                                  msg[FLD_REPLY], msg[FLD_REPLYCODE],
                                  msg[FLD_INRESPONSETO])
    elif msg[FLD_TYPE] == MSG_CLIENTREQUEST:
        proposalclient = Peer(*msg[FLD_PROPOSAL][0])
        proposal = Proposal(proposalclient, *msg[FLD_PROPOSAL][1:])
        return ClientRequestMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                                    proposal, msg[FLD_TOKEN])

p = Peer('123.456.34.32',14000,NODE_CLIENT)
helo = create_message(MSG_HELO, p,
                  {FLD_BALLOTNUMBER: (1,'1.2.3.4:14000'),
                   FLD_COMMANDNUMBER: 2578358375837538753,
                   FLD_SNAPSHOT: 12345})
clientreq = create_message(MSG_CLIENTREQUEST, p,
                           {FLD_PROPOSAL: Proposal(p, 678367836836738763876, 'kemal'),
                            FLD_TOKEN: 2345678})
clientrep = create_message(MSG_CLIENTREPLY, p,
                           {FLD_REPLY: '',
                            FLD_REPLYCODE: CR_REJECTED,
                            FLD_INRESPONSETO: 12345678996234567})
s = time.time()
parse_msg_if(clientreq)
print "Time spent with if: ", time.time()-s
s = time.time()
parse_msg_func(clientreq)
print "Time spent with func: ", time.time()-s
