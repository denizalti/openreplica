'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Initializes an OpenReplica instance
@copyright: See LICENSE
'''
import ast, _ast
import subprocess
import os, sys, time, shutil
from time import sleep,time
from optparse import OptionParser
from concoord.enums import *
from concoord.utils import *
from concoord.safetychecker import *
from concoord.proxygenerator import *
from concoord.openreplica.plmanager import *
from concoord.proxy.nameservercoord import *

# checks if a PL node is suitable for running a nameserver
def check_planetlab_dnsport(plconn, node):
    print "Uploading DNS tester to ", node
    pathtodnstester = CONCOORD_HELPERDIR+'testdnsport.py'
    plconn.uploadone(node, pathtodnstester)
    print "Trying to bind to DNS port"
    terminated, output = plconn.executecommandone(node, "sudo "+NPYTHONPATH+" testdnsport.py")
    success = terminated and output[1] == ''
    if success:
        print "DNS Port available on %s" % node
    else:
        print "DNS Port not available on %s" % node
    plconn.executecommandone(node, "rm testdnsport.py")
    return success,output

def check_planetlab_pythonversion(plconn, node):
    print "Checking python version on planetlab.."
    pathtopvtester = CONCOORD_HELPERDIR+'testpythonversion.py' 
    plconn.uploadone(node, pathtopvtester)
    terminated, output = plconn.executecommandone(node, NPYTHONPATH + " testpythonversion.py")
    success = terminated and output[1] == ''
    print "Success:", success
    print "Output:", output
    plconn.executecommandone(node, "rm testpythonversion.py")
    return success,output

def terminated(p):
    i = 5
    done = p.poll() is not None
    while not done and i>0:
        sleep(1)
        i -= 1
        done = p.poll() is not None
    return done

