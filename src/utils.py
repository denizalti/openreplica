import hashlib
import socket
import random
import struct

def findOwnIP():
    return socket.gethostbyname(socket.gethostname())

