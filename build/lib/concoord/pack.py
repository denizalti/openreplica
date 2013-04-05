"""
@author: Deniz Altinbuken
@note: Tuples used by ConCoord
@copyright: See LICENSE
"""
from collections import namedtuple

Proposal = namedtuple('Proposal', ['client', 'clientcommandnumber', 'command'])
<<<<<<< HEAD
ProposalClientBatch = namedtuple('ProposalClientBatch', ['client', 'clientcommandnumber', 'command'])
ProposalServerBatch = namedtuple('ProposalServerBatch', ['proposals'])

class Peer(namedtuple('Peer', ['addr', 'port', 'type'])):
        __slots__ = ()
        def __str__(self):
            return str((self.addr, self.port, self.type))
=======
ProposalBatch = namedtuple('ProposalBatch', ['proposals'])

Peer = namedtuple('Peer', ['addr', 'port', 'type'])
>>>>>>> deb1a242477c4e5184ae4bcd375ea72cf57058b7

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
<<<<<<< HEAD
                                               'proposal', 'serverbatch'])
=======
                                               'proposal', 'batch'])
>>>>>>> deb1a242477c4e5184ae4bcd375ea72cf57058b7
ProposeReplyMessage = namedtuple('ProposeReplyMessage', ['id', 'type',
                                                         'ballotnumber', 'inresponseto',
                                                         'commandnumber'])
PerformMessage = namedtuple('PerformMessage', ['id', 'type',
<<<<<<< HEAD
                                               'commandnumber', 'proposal',
					       'serverbatch', 'clientbatch'])

ClientRequestMessage = namedtuple('ClientRequestMessage', ['id', 'type', 'source',
                                                           'command', 'token',
                                                           'sendcount', 'clientbatch'])
=======
                                               'commandnumber', 'proposal', 'batch'])

ClientRequestMessage = namedtuple('ClientRequestMessage', ['id', 'type', 'source',
                                                           'command', 'token',
                                                           'sendcount'])
>>>>>>> deb1a242477c4e5184ae4bcd375ea72cf57058b7

ClientReplyMessage = namedtuple('ClientReplyMessage', ['id', 'type', 'source',
                                                       'reply', 'replycode', 'inresponseto'])

GarbageCollectMessage = namedtuple('GarbageCollectMessage', ['id', 'type',
                                                             'commandnumber', 'snapshot'])
