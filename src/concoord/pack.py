"""
@author: Deniz Altinbuken
@note: Tuples used by ConCoord
@copyright: See LICENSE
"""

from collections import namedtuple, OrderedDict

Proposal = namedtuple('Proposal', ['client', 'clientcommandnumber', 'command'])

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

'''
prepare = namedtuple('prepare', ['id', 'type', 'source', 'ballotnumber'])
prepare_adopted = namedtuple('prepare_adopted', ['id', 'type', 'source', 'ballotnumber'])
prepare_preempted = namedtuple('prepare_preempted', ['id', 'type', 'source', 'ballotnumber'])
propose = namedtuple('propose', ['id', 'type', 'source', 'ballotnumber'])
propose_accept = namedtuple('propose_accept', ['id', 'type', 'source', 'ballotnumber'])
propose_reject = namedtuple('propose_reject', ['id', 'type', 'source', 'ballotnumber'])
perform = namedtuple('propose_reject', ['id', 'type', 'source', 'ballotnumber'])
response = namedtuple('propose_reject', ['id', 'type', 'source', 'ballotnumber'])
clientrequest = namedtuple('clientrequest', ['id', 'type', 'source', 'ballotnumber'])
clientreply = namedtuple('clientreply', ['id', 'type', 'source', 'reply', 'replycode', 'inresponseto'])#
incclientrequest = namedtuple('incclientrequest', ['id', 'type', 'source', 'ballotnumber'])
garbagecollect = namedtuple('garbagecollect', ['id', 'type', 'source', 'commandnumber', 'snapshot'])#
status = namedtuple('status', ['id', 'type', 'source', 'ballotnumber'])
'''
