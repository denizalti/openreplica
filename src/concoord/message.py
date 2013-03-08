from concoord.pack import *
from concoord.enums import *
from concoord.pvalue import *
import msgpack
from threading import Lock

msgidpool = 0
msgidpool_lock = Lock()

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

def parse_basic(msg):
    src = Peer(*msg[FLD_SRC])
    return Message(msg[FLD_ID], msg[FLD_TYPE], src)

def parse_heloreply(msg):
    src = Peer(*msg[FLD_SRC])
    return Message(msg[FLD_ID], msg[FLD_TYPE], src, Peer(*msg[FLD_LEADER]))

def parse_clientrequest(msg):
    src = Peer(*msg[FLD_SRC])
    proposalclient = Peer(*msg[FLD_PROPOSAL][0])
    proposal = Proposal(proposalclient, *msg[FLD_PROPOSAL][1:])
    return ClientRequestMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                                proposal, msg[FLD_TOKEN], msg[FLD_SENDCOUNT])

def parse_clientreply(msg):
    src = Peer(*msg[FLD_SRC])
    return ClientReplyMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                              msg[FLD_REPLY], msg[FLD_REPLYCODE],
                              msg[FLD_INRESPONSETO])

def parse_prepare(msg):
    return PrepareMessage(msg[FLD_ID], msg[FLD_TYPE], msg[FLD_BALLOTNUMBER])

def parse_prepare_reply(msg):
    pvalueset = PValueSet()
    for index,pvalue in msg[FLD_PVALUESET].iteritems():
        pvalueset.pvalues[Proposal(*index[1])] = PValue(*pvalue)
    return PrepareReplyMessage(msg[FLD_ID], msg[FLD_TYPE],
                               msg[FLD_BALLOTNUMBER], msg[FLD_INRESPONSETO],
                               pvalueset)
def parse_propose(msg):
    if msg[FLD_BATCH]:
        proposal = ProposalBatch([])
        for p in msg[FLD_PROPOSAL][0]:
            pclient = Peer(*p[0])
            proposal.proposals.append(Proposal(pclient, *p[1:]))
    else:
        proposalclient = Peer(*msg[FLD_PROPOSAL][0])
        proposal = Proposal(proposalclient, *msg[FLD_PROPOSAL][1:])
    return ProposeMessage(msg[FLD_ID], msg[FLD_TYPE],
                          msg[FLD_BALLOTNUMBER], msg[FLD_COMMANDNUMBER],
                          proposal, msg[FLD_BATCH])


def parse_propose_reply(msg):
    return ProposeReplyMessage(msg[FLD_ID], msg[FLD_TYPE],
                               msg[FLD_BALLOTNUMBER], msg[FLD_INRESPONSETO],
                               msg[FLD_COMMANDNUMBER])

def parse_perform(msg):
    if msg[FLD_BATCH]:
        proposal = ProposalBatch([])
        for p in msg[FLD_PROPOSAL][0]: #XXX Why is this 0?
            pclient = Peer(*p[0])
            proposal.proposals.append(Proposal(pclient, *p[1:]))
    else:
        proposalclient = Peer(*msg[FLD_PROPOSAL][0])
        proposal = Proposal(proposalclient, *msg[FLD_PROPOSAL][1:])
    return PerformMessage(msg[FLD_ID], msg[FLD_TYPE],
                          msg[FLD_COMMANDNUMBER], proposal, msg[FLD_BATCH])

def parse_response(msg):
    src = Peer(*msg[FLD_SRC])
    return Message(msg[FLD_ID], msg[FLD_TYPE], src)

def parse_incclientrequest(msg):
    src = Peer(*msg[FLD_SRC])
    proposalclient = Peer(*msg[FLD_PROPOSAL][0])
    proposal = Proposal(proposalclient, *msg[FLD_PROPOSAL][1:])
    return ClientRequestMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                                proposal, msg[FLD_TOKEN])

def parse_updatereply(msg):
    for commandnumber,command in msg[FLD_DECISIONS].iteritems():
        proposalclient = Peer(*msg[FLD_DECISIONS][commandnumber][0])
        msg[FLD_DECISIONS][commandnumber] = Proposal(proposalclient,
                                                     *msg[FLD_DECISIONS][commandnumber][1:])
    return UpdateReplyMessage(msg[FLD_ID], msg[FLD_TYPE], msg[FLD_DECISIONS])

def parse_garbagecollect(msg):
    return GarbageCollectMessage(msg[FLD_ID], msg[FLD_TYPE],
                                 msg[FLD_COMMANDNUMBER], msg[FLD_SNAPSHOT])

def parse_message(msg):
    return parse_functions[msg[FLD_TYPE]](msg)

# XXX deprecated
def old_parse_message(msg):
    src = Peer(*msg[FLD_SRC])
    if msg[FLD_TYPE] == MSG_HELO or msg[FLD_TYPE] == MSG_PING \
            or msg[FLD_TYPE] == MSG_UPDATE or msg[FLD_TYPE] == MSG_STATUS:
        return Message(msg[FLD_ID], msg[FLD_TYPE], src)
    elif msg[FLD_TYPE] == MSG_CLIENTREQUEST:
        proposalclient = Peer(*msg[FLD_PROPOSAL][0])
        proposal = Proposal(proposalclient, *msg[FLD_PROPOSAL][1:])
        return ClientRequestMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                                    proposal, msg[FLD_TOKEN], msg[FLD_SENDCOUNT])
    elif msg[FLD_TYPE] == MSG_PROPOSE:
        if msg[FLD_BATCH]:
            proposal = ProposalBatch([])
            for p in msg[FLD_PROPOSAL][0]:
                pclient = Peer(*p[0])
                proposal.proposals.append(Proposal(pclient, *p[1:]))
        else:
            proposalclient = Peer(*msg[FLD_PROPOSAL][0])
            proposal = Proposal(proposalclient, *msg[FLD_PROPOSAL][1:])
        return ProposeMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                              msg[FLD_BALLOTNUMBER], msg[FLD_COMMANDNUMBER],
                              proposal, msg[FLD_BATCH])
    elif msg[FLD_TYPE] == MSG_PROPOSE_ACCEPT or msg[FLD_TYPE] == MSG_PROPOSE_REJECT:
        return ProposeReplyMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                                   msg[FLD_BALLOTNUMBER], msg[FLD_INRESPONSETO],
                                   msg[FLD_COMMANDNUMBER])
    elif msg[FLD_TYPE] == MSG_PERFORM:
        if msg[FLD_BATCH]:
            proposal = ProposalBatch([])
            for p in msg[FLD_PROPOSAL][0]:
                pclient = Peer(*p[0])
                proposal.proposals.append(Proposal(pclient, *p[1:]))
        else:
            proposalclient = Peer(*msg[FLD_PROPOSAL][0])
            proposal = Proposal(proposalclient, *msg[FLD_PROPOSAL][1:])
        return PerformMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                              msg[FLD_COMMANDNUMBER], proposal, msg[FLD_BATCH])
    elif msg[FLD_TYPE] == MSG_PREPARE:
        return PrepareMessage(msg[FLD_ID], msg[FLD_TYPE], src, msg[FLD_BALLOTNUMBER])
    elif msg[FLD_TYPE] == MSG_PREPARE_ADOPTED or msg[FLD_TYPE] == MSG_PREPARE_PREEMPTED:
        pvalueset = PValueSet()
        for index,pvalue in msg[FLD_PVALUESET].iteritems():
            pvalueset.pvalues[Proposal(*index[1])] = PValue(*pvalue)
        return PrepareReplyMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                                   msg[FLD_BALLOTNUMBER], msg[FLD_INRESPONSETO],
                                   pvalueset)
    elif msg[FLD_TYPE] == MSG_RESPONSE:
        return Message(msg[FLD_ID], msg[FLD_TYPE], src)
    elif msg[FLD_TYPE] == MSG_CLIENTREPLY:
        return ClientReplyMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                                  msg[FLD_REPLY], msg[FLD_REPLYCODE],
                                  msg[FLD_INRESPONSETO])
    elif msg[FLD_TYPE] == MSG_INCCLIENTREQUEST:
        proposalclient = Peer(*msg[FLD_PROPOSAL][0])
        proposal = Proposal(proposalclient, *msg[FLD_PROPOSAL][1:])
        return ClientRequestMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                                    proposal, msg[FLD_TOKEN])
    elif msg[FLD_TYPE] == MSG_UPDATEREPLY:
        for commandnumber,command in msg[FLD_DECISIONS].iteritems():
            proposalclient = Peer(*msg[FLD_DECISIONS][commandnumber][0])
            msg[FLD_DECISIONS][commandnumber] = Proposal(proposalclient,
                                                         *msg[FLD_DECISIONS][commandnumber][1:])
        return UpdateReplyMessage(msg[FLD_ID], msg[FLD_TYPE], src, msg[FLD_DECISIONS])
    elif msg[FLD_TYPE] == MSG_GARBAGECOLLECT:
        return GarbageCollectMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                                     msg[FLD_COMMANDNUMBER], msg[FLD_SNAPSHOT])

parse_functions = [
    parse_prepare, # MSG_PREPARE
    parse_prepare_reply, # MSG_PREPARE_ADOPTED
    parse_prepare_reply, # MSG_PREPARE_PREEMPTED
    parse_propose, # MSG_PROPOSE
    parse_propose_reply, # MSG_PROPOSE_ACCEPT
    parse_propose_reply, # MSG_PROPOSE_REJECT
    
    parse_basic, # MSG_HELO
    parse_heloreply, # MSG_HELOREPLY
    parse_basic, # MSG_PING

    parse_basic, # MSG_UPDATE
    parse_updatereply, # MSG_UPDATEREPLY

    parse_perform, # MSG_PERFORM
    parse_response, # MSG_RESPONSE

    parse_clientrequest, # MSG_CLIENTREQUEST
    parse_clientreply, # MSG_CLIENTREPLY
    parse_incclientrequest, # MSG_INCCLIENTREQUEST
    parse_garbagecollect,  # MSG_GARBAGECOLLECT
    parse_basic           # MSG_STATUS
    ]

