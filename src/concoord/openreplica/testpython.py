'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Script to check Python installation
@date: November 24, 2011
@copyright: See COPYING.txt
'''
import socket, sys
import string
from plmanager import *

def checkpythonversion(plconn, node):
    command = 'python --version'
    rtv, output = plconn.executecommandone(node, command)
    if rtv:
        for out in output:
            if string.find(out, 'Python 2.7') > 0:
                return True
    return False
    
def main():
    if len(sys.argv) == 1:
        print 'Usage: testpython nodename'
        os._exit(2)
    node = sys.argv[1]
    plconn = PLConnection(nodes=[node])
    if checkpythonversion(plconn, node):
        return 0
    return 1
    
if __name__=='__main__':
    sys.exit(main())
