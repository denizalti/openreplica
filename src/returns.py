from threading import Lock
from message import Message, PaxosMessage, HandshakeMessage, AckMessage, ClientMessage, ClientReplyMessage, UpdateMessage
from connection import Connection, ConnectionPool
from enums import *

def return_outofband(designated, owner, command):
    if not designated:
        return
    clientreply = ClientReplyMessage(MSG_CLIENTMETAREPLY, owner.me, replycode=CR_METAREPLY, inresponseto=command.clientcommandnumber)
    destconn = owner.clientpool.get_connection_by_peer(command.client)
    if destconn.thesocket == None:
        return
    destconn.send(clientreply)
