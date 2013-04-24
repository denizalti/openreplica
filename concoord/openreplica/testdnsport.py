'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Script to check DNS Port bindings
@copyright: See LICENSE
'''
import socket
import sys

def testdnsport():
    addr = 'localhost'
    port = 53
    thesocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    thesocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    thesocket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
    thesocket.setblocking(0)
    try:
        thesocket.bind((addr,port))
    except socket.error:
        return 1
    thesocket.close()
    return 0

if __name__=='__main__':
    sys.exit(testdnsport())
