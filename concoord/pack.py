"""
@author: Deniz Altinbuken
@note: Tuples used by ConCoord
@copyright: See LICENSE
"""
from collections import namedtuple

Proposal = namedtuple('Proposal', ['client', 'clientcommandnumber', 'command'])
ProposalClientBatch = namedtuple('ProposalClientBatch', ['client', 'clientcommandnumber', 'command'])
ProposalServerBatch = namedtuple('ProposalServerBatch', ['proposals'])

class Peer(namedtuple('Peer', ['addr', 'port', 'type'])):
        __slots__ = ()
        def __str__(self):
            return str((self.addr, self.port, self.type))

PValue = namedtuple('PValue', ['ballotnumber', 'commandnumber', 'proposal'])
Message = namedtuple('Message', ['id', 'type', 'source'])
IssueMessage = namedtuple('IssueMessage', ['id', 'type', 'source'])
StatusMessage = namedtuple('StatusMessage', ['id', 'type', 'source'])
HeloReplyMessage = namedtuple('HeloReplyMessage', ['id', 'type', 'source', 'leader'])
UpdateReplyMessage = namedtuple('UpdateReplyMessage', ['id', 'type', 'decisions'])
PrepareMessage = namedtuple('PrepareMessage', ['id', 'type', 'ballotnumber'])
PrepareReplyMessage = namedtuple('PrepareReplyMessage', ['id', 'type',
                                                         'ballotnumber', 'inresponseto',
                                                         'pvalueset'])
ProposeMessage = namedtuple('ProposeMessage', ['id', 'type',
                                               'ballotnumber', 'commandnumber',
                                               'proposal', 'serverbatch'])
ProposeReplyMessage = namedtuple('ProposeReplyMessage', ['id', 'type',
                                                         'ballotnumber', 'inresponseto',
                                                         'commandnumber'])
PerformMessage = namedtuple('PerformMessage', ['id', 'type',
                                               'commandnumber', 'proposal',
					       'serverbatch', 'clientbatch'])

ClientRequestMessage = namedtuple('ClientRequestMessage', ['id', 'type', 'source',
                                                           'command', 'token',
                                                           'sendcount', 'clientbatch'])

ClientReplyMessage = namedtuple('ClientReplyMessage', ['id', 'type', 'source',
                                                       'reply', 'replycode', 'inresponseto'])

GarbageCollectMessage = namedtuple('GarbageCollectMessage', ['id', 'type',
                                                             'commandnumber', 'snapshot'])
