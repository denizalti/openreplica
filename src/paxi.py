from connection import Connection, ConnectionPool

def return_outofband(source, clientcommandnumber, destinations, retval):
    for dest in destinations:
        clientreply = ClientMessage(MSG_CLIENTMETAREPLY, source.me, retval, clientcommandnumber)
        destconn = source.clientpool.get_connection_by_peer(dest)
        if destconn.thesocket == None:
            return
        destconn.send(clientreply)


RCODE_UNBLOCK, RCODE_BLOCK_UNTIL_NOTICE = range(2)
