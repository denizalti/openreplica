'''
@author: deniz
@note: Script to check DNS Port bindings
@date: November 20, 2011
'''
import socket
import sys

def testdnsport():
    addr = '127.0.0.1'
    port = 53
    thesocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    thesocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    thesocket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
    thesocket.setblocking(0)
    try:
        thesocket.bind((addr,port))
    except socket.error:
        return False
    thesocket.close()
    return True
    
def main():
    print testdnsport()
    
if __name__=='__main__':
    sys.exit(main())
