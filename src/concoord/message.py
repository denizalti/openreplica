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

def parse_message(msg):
    src = Peer(*msg[FLD_SRC])
    if msg[FLD_TYPE] == MSG_HELO or msg[FLD_TYPE] == MSG_PING or msg[FLD_TYPE] == MSG_BYE \
            or msg[FLD_TYPE] == MSG_UPDATE or msg[FLD_TYPE] == MSG_STATUS:
        return Message(msg[FLD_ID], msg[FLD_TYPE], src)
    elif msg[FLD_TYPE] == MSG_CLIENTREQUEST:
        proposalclient = Peer(*msg[FLD_PROPOSAL][0])
        proposal = Proposal(proposalclient, *msg[FLD_PROPOSAL][1:])
        return ClientRequestMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                                    proposal, msg[FLD_TOKEN])
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
