import socket

def findOwnIP():
    return socket.gethostbyname(socket.gethostname())

