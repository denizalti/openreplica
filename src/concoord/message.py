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
    with msgidpool_lock:
        m[MSGID] = msgidpool
        msgidpool += 1
    m[MSGTYPE] = msgtype
>>>>>>> 2f8b951ccb2db6fa49402864ebeaa13d974cc2ac
    m[MSGSRC] = src
    return m

def parse_message(msg):
    src = Peer(*msg[MSGSRC])
    if msg[MSGTYPE] == MSG_HELO or msg[MSGTYPE] == MSG_PING or msg[MSGTYPE] == MSG_BYE \
            or msg[MSGTYPE] == MSG_UPDATE or msg[MSGTYPE] == MSG_STATUS:
        return Message(msg[MSGID], msg[MSGTYPE], src)
    elif msg[MSGTYPE] == MSG_CLIENTREQUEST:
        proposalclient = Peer(*msg[PROPOSAL][0])
        proposal = Proposal(proposalclient, *msg[PROPOSAL][1:])
        return ClientRequestMessage(msg[MSGID], msg[MSGTYPE], src,
                                    proposal, msg[TOKEN])
    elif msg[MSGTYPE] == MSG_PROPOSE:
        print "Message is BATCHED: ", msg[BATCH]
        if msg[BATCH]:
            # XXX Go through proposals and cast them to Proposal
            proposal = ProposalBatch([])
            for p in msg[PROPOSAL][0]: #XXX Why is this 0?
                pclient = Peer(*p[0])
                proposal.proposals.append(Proposal(pclient, *p[1:]))
        else:
            proposalclient = Peer(*msg[PROPOSAL][0])
            proposal = Proposal(proposalclient, *msg[PROPOSAL][1:])
        print "Proposal: ", proposal
        return ProposeMessage(msg[MSGID], msg[MSGTYPE], src,
                              msg[BALLOTNUMBER], msg[COMMANDNUMBER],
                              proposal, msg[BATCH])
    elif msg[MSGTYPE] == MSG_PROPOSE_ACCEPT or msg[MSGTYPE] == MSG_PROPOSE_REJECT:
        return ProposeReplyMessage(msg[MSGID], msg[MSGTYPE], src,
                                   msg[BALLOTNUMBER], msg[INRESPONSETO],
                                   msg[COMMANDNUMBER])
    elif msg[MSGTYPE] == MSG_PERFORM:
        if msg[BATCH]:
            # XXX Go through proposals and cast them to Proposal
            proposal = ProposalBatch([])
            for p in msg[PROPOSAL][0]:
                pclient = Peer(*p[0])
                proposal.proposals.append(Proposal(pclient, *p[1:]))
        else:
            proposalclient = Peer(*msg[PROPOSAL][0])
            proposal = Proposal(proposalclient, *msg[PROPOSAL][1:])
        return PerformMessage(msg[MSGID], msg[MSGTYPE], src,
                              msg[COMMANDNUMBER], proposal, msg[BATCH])
    elif msg[MSGTYPE] == MSG_PREPARE:
        return PrepareMessage(msg[MSGID], msg[MSGTYPE], src, msg[BALLOTNUMBER])
    elif msg[MSGTYPE] == MSG_PREPARE_ADOPTED or msg[MSGTYPE] == MSG_PREPARE_PREEMPTED:
        pvalueset = PValueSet()
        for index,pvalue in msg[PVALUESET].iteritems():
            pvalueset.pvalues[Proposal(*index[1])] = PValue(*pvalue)
        return PrepareReplyMessage(msg[MSGID], msg[MSGTYPE], src,
                                   msg[BALLOTNUMBER], msg[INRESPONSETO],
                                   pvalueset)
    elif msg[MSGTYPE] == MSG_RESPONSE:
        return Message(msg[MSGID], msg[MSGTYPE], src)
    elif msg[MSGTYPE] == MSG_CLIENTREPLY:
        return ClientReplyMessage(msg[MSGID], msg[MSGTYPE], src,
                                  msg[REPLY], msg[REPLYCODE],
                                  msg[INRESPONSETO])
    elif msg[MSGTYPE] == MSG_INCCLIENTREQUEST:
        proposalclient = Peer(*msg[PROPOSAL][0])
        proposal = Proposal(proposalclient, *msg[PROPOSAL][1:])
        return ClientRequestMessage(msg[MSGID], msg[MSGTYPE], src,
                                    proposal, msg[TOKEN])
    elif msg[MSGTYPE] == MSG_UPDATEREPLY:
        for commandnumber,command in msg[DECISIONS].iteritems():
            proposalclient = Peer(*msg[DECISIONS][commandnumber][0])
            msg[DECISIONS][commandnumber] = Proposal(proposalclient, *msg[DECISIONS][commandnumber][1:])
        return UpdateReplyMessage(msg[MSGID], msg[MSGTYPE], src, msg[DECISIONS])
    elif msg[MSGTYPE] == MSG_GARBAGECOLLECT:
        return GarbageCollectMessage(msg[MSGID], msg[MSGTYPE], src, msg[COMMANDNUMBER], msg[SNAPSHOT])
