"""
@author: Deniz Altinbuken
@note: Tuples used by ConCoord
@copyright: See LICENSE
"""
from collections import namedtuple
import six

def fix_incoming(data):
    if six.PY2:
        return data
    if isinstance(data, tuple) and isinstance(getattr(data, '_fields', None), tuple):
        # This is a namedtuple, see http://bugs.python.org/issue7796
        return data
    if isinstance(data, bytes):
        return data.decode('latin1')
    elif isinstance(data, tuple):
        return tuple(fix_incoming(x) for x in data)
    else:
        return data

class Proposal(namedtuple('Proposal', ['client', 'clientcommandnumber', 'command'])):
    __slots__ = ()
    def __new__(_cls, *args):
        args = fix_incoming(args)
        return tuple.__new__(_cls, args)


class ProposalClientBatch(namedtuple('ProposalClientBatch', 
                                     ['client', 'clientcommandnumber', 'command'])):
    __slots__ = ()
    def __new__(_cls, *args):
        args = fix_incoming(args)
        return tuple.__new__(_cls, args)


ProposalServerBatch = namedtuple('ProposalServerBatch', ['proposals'])

class Peer(namedtuple('Peer', ['addr', 'port', 'type'])):
    __slots__ = ()
    def __str__(self):
        return str((self.addr, self.port, self.type))

    def __new__(_cls, *args):
        args = fix_incoming(args)
        return tuple.__new__(_cls, args)

class PValue(namedtuple('PValue', ['ballotnumber', 'commandnumber', 'proposal'])):
    __slots__ = ()
    def __new__(_cls, *args):
        args = fix_incoming(args)
        return tuple.__new__(_cls, args)


Message = namedtuple('Message', ['id', 'type', 'source'])
IssueMessage = namedtuple('IssueMessage', ['id', 'type', 'source'])
StatusMessage = namedtuple('StatusMessage', ['id', 'type', 'source'])
HeloReplyMessage = namedtuple('HeloReplyMessage', ['id', 'type', 'source', 'leader'])

class UpdateReplyMessage(namedtuple('UpdateReplyMessage', ['id', 'type', 'source', 'decisions'])):
    __slots__ = ()
    def __new__(_cls, *args):
        args = fix_incoming(args)
        return tuple.__new__(_cls, args)

class PrepareMessage(namedtuple('PrepareMessage', ['id', 'type', 'source', 'ballotnumber'])):
    __slots__ = ()
    def __new__(_cls, *args):
        args = fix_incoming(args)
        return tuple.__new__(_cls, args)


class PrepareReplyMessage(namedtuple('PrepareReplyMessage', 
                                     ['id', 'type', 'source', 'ballotnumber', 'inresponseto',
                                      'pvalueset'])):
    __slots__ = ()
    def __new__(_cls, *args):
        args = fix_incoming(args)
        return tuple.__new__(_cls, args)


class ProposeMessage(namedtuple('ProposeMessage', 
                                ['id', 'type', 'source', 'ballotnumber', 'commandnumber',
                                 'proposal', 'serverbatch'])):
    __slots__ = ()    
    def __new__(_cls, *args):
        args = fix_incoming(args)
        return tuple.__new__(_cls, args)
    
class ProposeReplyMessage(namedtuple('ProposeReplyMessage', 
                                     ['id', 'type', 'source', 'ballotnumber', 'inresponseto',
                                      'commandnumber'])):
    __slots__ = ()    
    def __new__(_cls, *args):
        args = fix_incoming(args)
        return tuple.__new__(_cls, args)


    
class PerformMessage(namedtuple('PerformMessage', ['id', 'type', 'source',
                                               'commandnumber', 'proposal',
					       'serverbatch', 'clientbatch'])):
    __slots__ = ()    
    def __new__(_cls, *args):
        args = fix_incoming(args)
        return tuple.__new__(_cls, args)

class ClientRequestMessage(namedtuple('ClientRequestMessage', 
                                      ['id', 'type', 'source','command', 'token',
                                       'sendcount', 'clientbatch'])):
    __slots__ = ()    
    def __new__(_cls, *args):
        args = fix_incoming(args)
        return tuple.__new__(_cls, args)



class ClientReplyMessage(namedtuple('ClientReplyMessage', 
                                    ['id', 'type', 'source',
                                     'reply', 'replycode', 'inresponseto'])):
    __slots__ = ()    
    def __new__(_cls, *args):
        args = fix_incoming(args)
        return tuple.__new__(_cls, args)



class GarbageCollectMessage(namedtuple('GarbageCollectMessage', ['id', 'type', 'source',
                                                             'commandnumber', 'snapshot'])):
    __slots__ = ()    
    def __new__(_cls, *args):
        args = fix_incoming(args)
        return tuple.__new__(_cls, args)

