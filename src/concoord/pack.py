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


