"""
@author: Deniz Altinbuken
@note: Tuples used by ConCoord
@copyright: See LICENSE
"""
from collections import namedtuple

Proposal = namedtuple('Proposal', ['client', 'clientcommandnumber', 'command'])
ProposalBatch = namedtuple('ProposalBatch', ['proposals'])

Peer = namedtuple('Peer', ['addr', 'port', 'type'])
def getpeerid(peer):
    return '%s:%d' % (peer.addr, peer.port)

PValue = namedtuple('PValue', ['ballotnumber', 'commandnumber', 'proposal'])
Message = namedtuple('Message', ['id', 'type', 'source'])
UpdateReplyMessage = namedtuple('UpdateReplyMessage', ['id', 'type', 'source', 'decisions'])
PrepareMessage = namedtuple('PrepareMessage', ['id', 'type', 'source', 'ballotnumber'])
PrepareReplyMessage = namedtuple('PrepareReplyMessage', ['id', 'type', 'source',
                                                         'ballotnumber', 'inresponseto',
                                                         'pvalueset'])
ProposeMessage = namedtuple('ProposeMessage', ['id', 'type', 'source',
                                               'ballotnumber', 'commandnumber',
                                               'proposal', 'batch'])
ProposeReplyMessage = namedtuple('ProposeReplyMessage', ['id', 'type', 'source',
                                                         'ballotnumber', 'inresponseto',
                                                         'commandnumber'])
PerformMessage = namedtuple('PerformMessage', ['id', 'type', 'source',
                                               'commandnumber', 'proposal', 'batch'])

ClientRequestMessage = namedtuple('ClientRequestMessage', ['id', 'type', 'source',
                                                           'command', 'token',
                                                           'sendcount'])

ClientReplyMessage = namedtuple('ClientReplyMessage', ['id', 'type', 'source',
                                                       'reply', 'replycode', 'inresponseto'])

GarbageCollectMessage = namedtuple('GarbageCollectMessage', ['id', 'type', 'source',
                                                             'commandnumber', 'snapshot'])
