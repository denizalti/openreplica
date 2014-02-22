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
    src = Peer(msg[FLD_SRC][0], msg[FLD_SRC][1], msg[FLD_SRC][2])
    return Message(msg[FLD_ID], msg[FLD_TYPE], src)

def parse_heloreply(msg):
    src = Peer(msg[FLD_SRC][0], msg[FLD_SRC][1], msg[FLD_SRC][2])
    return HeloReplyMessage(msg[FLD_ID], msg[FLD_TYPE],
                            src, Peer(msg[FLD_LEADER][0],
                                      msg[FLD_LEADER][1],
                                      msg[FLD_LEADER][2]))

def parse_clientrequest(msg):
    src = Peer(msg[FLD_SRC][0], msg[FLD_SRC][1], msg[FLD_SRC][2])
    if msg[FLD_CLIENTBATCH]:
        proposal = ProposalClientBatch(msg[FLD_PROPOSAL][0],
                                       msg[FLD_PROPOSAL][1],
                                       msg[FLD_PROPOSAL][2])
    else:
        proposal = Proposal(msg[FLD_PROPOSAL][0],
                            msg[FLD_PROPOSAL][1],
                            msg[FLD_PROPOSAL][2])

    return ClientRequestMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                                proposal, msg[FLD_TOKEN],
                                msg[FLD_SENDCOUNT], msg[FLD_CLIENTBATCH])

def parse_clientreply(msg):
    src = Peer(msg[FLD_SRC][0], msg[FLD_SRC][1], msg[FLD_SRC][2])
    return ClientReplyMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                              msg[FLD_REPLY], msg[FLD_REPLYCODE],
                              msg[FLD_INRESPONSETO])

def parse_prepare(msg):
    src = Peer(msg[FLD_SRC][0], msg[FLD_SRC][1], msg[FLD_SRC][2])
    return PrepareMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                          msg[FLD_BALLOTNUMBER])

def parse_prepare_reply(msg):
    src = Peer(msg[FLD_SRC][0], msg[FLD_SRC][1], msg[FLD_SRC][2])
    pvalueset = PValueSet()
    for index,pvalue in msg[FLD_PVALUESET].iteritems():
        pvalueset.pvalues[Proposal(index[1][0],
                                   index[1][1],
                                   index[1][2])] = PValue(pvalue[0], pvalue[1], pvalue[2])
    return PrepareReplyMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                               msg[FLD_BALLOTNUMBER], msg[FLD_INRESPONSETO],
                               pvalueset)
def parse_propose(msg):
    src = Peer(msg[FLD_SRC][0], msg[FLD_SRC][1], msg[FLD_SRC][2])
    if msg[FLD_SERVERBATCH]:
        proposal = ProposalServerBatch([])
        for p in msg[FLD_PROPOSAL][0]:
            proposal.proposals.append(Proposal(p[0], p[1], p[2]))
    else:
        proposal = Proposal(msg[FLD_PROPOSAL][0], msg[FLD_PROPOSAL][1], msg[FLD_PROPOSAL][2])
    return ProposeMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                          msg[FLD_BALLOTNUMBER], msg[FLD_COMMANDNUMBER],
                          proposal, msg[FLD_SERVERBATCH])


def parse_propose_reply(msg):
    src = Peer(msg[FLD_SRC][0], msg[FLD_SRC][1], msg[FLD_SRC][2])
    return ProposeReplyMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                               msg[FLD_BALLOTNUMBER], msg[FLD_INRESPONSETO],
                               msg[FLD_COMMANDNUMBER])

def parse_perform(msg):
    src = Peer(msg[FLD_SRC][0], msg[FLD_SRC][1], msg[FLD_SRC][2])
    if msg[FLD_SERVERBATCH]:
        proposal = ProposalServerBatch([])
        for p in msg[FLD_PROPOSAL][0]:
            pclient = Peer(p[0][0], p[0][1], p[0][2])
            proposal.proposals.append(Proposal(pclient, p[1], p[2]))
    elif msg[FLD_CLIENTBATCH]:
        proposalclient = Peer(msg[FLD_PROPOSAL][0][0], msg[FLD_PROPOSAL][0][1], msg[FLD_PROPOSAL][0][2])
        proposal = ProposalClientBatch(proposalclient, msg[FLD_PROPOSAL][1], msg[FLD_PROPOSAL][2])
    else:
        proposalclient = Peer(msg[FLD_PROPOSAL][0][0], msg[FLD_PROPOSAL][0][1], msg[FLD_PROPOSAL][0][2])
        proposal = Proposal(proposalclient, msg[FLD_PROPOSAL][1], msg[FLD_PROPOSAL][2])
    return PerformMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                          msg[FLD_COMMANDNUMBER], proposal,
                          msg[FLD_SERVERBATCH], msg[FLD_CLIENTBATCH])

def parse_response(msg):
    src = Peer(msg[FLD_SRC][0], msg[FLD_SRC][1], msg[FLD_SRC][2])
    return Message(msg[FLD_ID], msg[FLD_TYPE], src)

def parse_incclientrequest(msg):
    src = Peer(msg[FLD_SRC][0], msg[FLD_SRC][1], msg[FLD_SRC][2])
    proposalclient = Peer(msg[FLD_PROPOSAL][0][0], msg[FLD_PROPOSAL][0][1], msg[FLD_PROPOSAL][0][2])
    proposal = Proposal(proposalclient, msg[FLD_PROPOSAL][1], msg[FLD_PROPOSAL][2])
    return ClientRequestMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                                proposal, msg[FLD_TOKEN])

def parse_updatereply(msg):
    src = Peer(msg[FLD_SRC][0], msg[FLD_SRC][1], msg[FLD_SRC][2])
    for commandnumber,command in msg[FLD_DECISIONS].iteritems():
        try:
            msg[FLD_DECISIONS][commandnumber] = Proposal(msg[FLD_DECISIONS][commandnumber][0],
                                                         msg[FLD_DECISIONS][commandnumber][1],
                                                         msg[FLD_DECISIONS][commandnumber][2])
        except IndexError as i:
            msg[FLD_DECISIONS][commandnumber] = Proposal(msg[FLD_DECISIONS][commandnumber][0][0][0],
                                                         msg[FLD_DECISIONS][commandnumber][0][0][1],
                                                         msg[FLD_DECISIONS][commandnumber][0][0][2])
    return UpdateReplyMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                              msg[FLD_DECISIONS])

def parse_garbagecollect(msg):
    src = Peer(msg[FLD_SRC][0], msg[FLD_SRC][1], msg[FLD_SRC][2])
    return GarbageCollectMessage(msg[FLD_ID], msg[FLD_TYPE], src,
                                 msg[FLD_COMMANDNUMBER], msg[FLD_SNAPSHOT])

def parse_message(msg):
    return parse_functions[msg[FLD_TYPE]](msg)

parse_functions = [
    parse_clientrequest, # MSG_CLIENTREQUEST
    parse_clientreply, # MSG_CLIENTREPLY
    parse_incclientrequest, # MSG_INCCLIENTREQUEST

    parse_prepare, # MSG_PREPARE
    parse_prepare_reply, # MSG_PREPARE_ADOPTED
    parse_prepare_reply, # MSG_PREPARE_PREEMPTED
    parse_propose, # MSG_PROPOSE
    parse_propose_reply, # MSG_PROPOSE_ACCEPT
    parse_propose_reply, # MSG_PROPOSE_REJECT

    parse_basic, # MSG_HELO
    parse_heloreply, # MSG_HELOREPLY
    parse_basic, # MSG_PING
    parse_basic, # MSG_PINGREPLY

    parse_basic, # MSG_UPDATE
    parse_updatereply, # MSG_UPDATEREPLY

    parse_perform, # MSG_PERFORM
    parse_response, # MSG_RESPONSE

    parse_garbagecollect,  # MSG_GARBAGECOLLECT
    parse_basic,           # MSG_STATUS
    parse_basic            # MSG_ISSUE
    ]

