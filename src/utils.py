import socket

def findOwnIP():
    """Retrieves the hostname of the caller"""
    return socket.gethostbyname(socket.gethostname())

