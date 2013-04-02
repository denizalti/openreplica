"""
@author: Deniz Altinbuken
@note: Tuples used by ConCoord
@copyright: See LICENSE
"""
from collections import namedtuple

Proposal = namedtuple('Proposal', ['client', 'clientcommandnumber', 'command'])
ProposalBatch = namedtuple('ProposalBatch', ['proposals'])

Peer = namedtuple('Peer', ['addr', 'port', 'type'])

PValue = namedtuple('PValue', ['ballotnumber', 'commandnumber', 'proposal'])
Message = namedtuple('Message', ['id', 'type', 'source'])
HeloReplyMessage = namedtuple('HeloReplyMessage', ['id', 'type', 'source', 'leader'])
UpdateReplyMessage = namedtuple('UpdateReplyMessage', ['id', 'type', 'decisions'])
PrepareMessage = namedtuple('PrepareMessage', ['id', 'type', 'ballotnumber'])
PrepareReplyMessage = namedtuple('PrepareReplyMessage', ['id', 'type',
                                                         'ballotnumber', 'inresponseto',
                                                         'pvalueset'])
ProposeMessage = namedtuple('ProposeMessage', ['id', 'type',
                                               'ballotnumber', 'commandnumber',
                                               'proposal', 'batch'])
ProposeReplyMessage = namedtuple('ProposeReplyMessage', ['id', 'type',
                                                         'ballotnumber', 'inresponseto',
                                                         'commandnumber'])
PerformMessage = namedtuple('PerformMessage', ['id', 'type',
                                               'commandnumber', 'proposal', 'batch'])

ClientRequestMessage = namedtuple('ClientRequestMessage', ['id', 'type', 'source',
                                                           'command', 'token',
                                                           'sendcount'])

ClientReplyMessage = namedtuple('ClientReplyMessage', ['id', 'type', 'source',
                                                       'reply', 'replycode', 'inresponseto'])

GarbageCollectMessage = namedtuple('GarbageCollectMessage', ['id', 'type',
                                                             'commandnumber', 'snapshot'])
