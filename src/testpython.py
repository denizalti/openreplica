'''
@author: deniz
@note: Script to check Python installation
@date: November 24, 2011
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

def installpython(plconn, node):
    print "uploading python source"
    pythonpath = '/Users/denizalti/paxi/python/Python-2.7.tgz'
    success = plconn.uploadone(node, pythonpath)
    if not success:
        print "Cannot upload."
        return False
    print "extracting"
    success, output = plconn.executecommandone(node, "tar xzf Python-2.7.tgz")
    print output
    if not success:
        print "Cannot extract."
        return False
    print "configuring"
    success, output = plconn.executecommandone(node, "./Python-2.7/configure")
    print output
    if not success:
        print "Cannot configure."
        return False
    print "making"
    success, output = plconn.executecommandone(node, "make -C ./Python-2.7")
    print output
    if not success:
        print "Cannot make."
        return False
    print "installing"
    success, output = plconn.executecommandone(node, "make install -C ./Python-2.7")
    print output
    if not success:
        print "Cannot make."
        return False
    
def main():
    if len(sys.argv) == 1:
        print 'Give a node'
        return 2
    node = sys.argv[1]
    plconn = PLConnection(nodes=[node])
    pythonnew = checkpythonversion(plconn, node)
    if pythonnew:
        print "good to go"
        return True
    else:
        installpython(plconn, node)
    
if __name__=='__main__':
    sys.exit(main())
