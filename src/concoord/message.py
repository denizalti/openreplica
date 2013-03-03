from concoord.pack import *
from concoord.enums import *
from concoord.pvalue import *
import msgpack
from threading import Lock

msgidpool = 0
msgidpool_lock = Lock()

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

def assignuniqueid():
    global msgidpool
    global msgidpool_lock
    with msgidpool_lock:
        tempid = msgidpool
        msgidpool += 1
    return tempid

def create_message(msgtype, src, msgfields={}):
    global msgidpool
    global msgidpool_lock

    m = msgfields
    m[FLD_ID] = assignuniqueid()
    m[FLD_TYPE] = msgtype
    m[FLD_SRC] = src
    return m

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

def parse_prepare(msg, src):
    return PrepareMessage(msg[FLD_ID], msg[FLD_TYPE], src, msg[FLD_BALLOTNUMBER])

def parse_prepare_reply(msg, src):
    pvalueset = PValueSet()
    for index,pvalue in msg[FLD_PVALUESET].iteritems():
        pvalueset.pvalues[Proposal(*index[1])] = PValue(*pvalue)
    return PrepareReplyMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                               msg[FLD_BALLOTNUMBER], msg[FLD_INRESPONSETO],
                               pvalueset)
def parse_propose(msg, src):
    print "Message is BATCHED: ", msg[FLD_BATCH]
    if msg[FLD_BATCH]:
        proposal = ProposalBatch([])
        for p in msg[FLD_PROPOSAL][0]: #XXX Why is this 0?
            pclient = Peer(*p[0])
            proposal.proposals.append(Proposal(pclient, *p[1:]))
    else:
        proposalclient = Peer(*msg[FLD_PROPOSAL][0])
        proposal = Proposal(proposalclient, *msg[FLD_PROPOSAL][1:])
    print "Proposal: ", proposal
    return ProposeMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                          msg[FLD_BALLOTNUMBER], msg[FLD_COMMANDNUMBER],
                          proposal, msg[FLD_BATCH])


def parse_propose_reply(msg, src):
    return ProposeReplyMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                               msg[FLD_BALLOTNUMBER], msg[FLD_INRESPONSETO],
                               msg[FLD_COMMANDNUMBER])

def parse_perform(msg, src):
    if msg[FLD_BATCH]:
        proposal = ProposalBatch([])
        for p in msg[FLD_PROPOSAL][0]: #XXX Why is this 0?
            pclient = Peer(*p[0])
            proposal.proposals.append(Proposal(pclient, *p[1:]))
    else:
        proposalclient = Peer(*msg[FLD_PROPOSAL][0])
        proposal = Proposal(proposalclient, *msg[FLD_PROPOSAL][1:])
    return PerformMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                          msg[FLD_COMMANDNUMBER], proposal, msg[FLD_BATCH])

def parse_response(msg, src):
    return Message(msg[FLD_ID], msg[FLD_TYPE], src)

def parse_incclientrequest(msg,src):
    proposalclient = Peer(*msg[FLD_PROPOSAL][0])
    proposal = Proposal(proposalclient, *msg[FLD_PROPOSAL][1:])
    return ClientRequestMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                                proposal, msg[FLD_TOKEN])

def parse_updatereply(msg, src):
    for commandnumber,command in msg[FLD_DECISIONS].iteritems():
        proposalclient = Peer(*msg[FLD_DECISIONS][commandnumber][0])
        msg[FLD_DECISIONS][commandnumber] = Proposal(proposalclient,
                                                     *msg[FLD_DECISIONS][commandnumber][1:])
    return UpdateReplyMessage(msg[FLD_ID], msg[FLD_TYPE], src, msg[FLD_DECISIONS])

def parse_garbagecollect(msg, src):
    return GarbageCollectMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                                 msg[FLD_COMMANDNUMBER], msg[FLD_SNAPSHOT])

def parse_message(msg):
    src = Peer(*msg[FLD_SRC])
    return eval(parse_functions[msg[FLD_TYPE]])(msg, src)
