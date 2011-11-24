'''
@author: deniz
@note: Initializes an OpenReplica instance
@date: November 18, 2011
'''
from optparse import OptionParser
from time import sleep,time
import os, sys, time
import ast, _ast
import subprocess
from plmanager import *
from safetychecker import *
from proxygenerator import *
from openreplicacoordobjproxy import *

parser = OptionParser(usage="usage: %prog -s subdomain -n objectname -o objectcode -r replicas")
parser.add_option("-s", "--subdomain", action="store", dest="subdomain", help="name for the subdomain to reach openreplica")
parser.add_option("-n", "--objectfilename", action="store", dest="objectfilename", help="client object file name")
parser.add_option("-c", "--classname", action="store", dest="classname", help="main class name")
parser.add_option("-o", "--objectcode", action="store", dest="objectcode", help="client object code")
parser.add_option("-r", "--replicas", action="store", dest="replicanum", default=1, help="number of replicas")
(options, args) = parser.parse_args()

def create_objectfilefromcode(objectfilename, objectcode):
    print "[1] creating object file from code"
    try:
        abspath = os.path.abspath(objectfilename)
        objectfile = open(abspath, "w")
        objectfile.write(objectcode)
        objectfile.close()
        return objectfile
    except:
        return None

def create_objectfilefromfile(objectfilename):
    # For this function the object should be in the same
    # folder as the initializer
    print "[1] creating object file from file"
    try:
        abspath = os.path.abspath(objectfilename)
        objectfile = open(abspath, "r")
        objectfile.close()
        return objectfile
    except:
        return None

def check_object(clientobjectfile):
    print "[2] checking object safety"
    astnode = compile(open(clientobjectfile.name, 'rU').read(),"<string>","exec",_ast.PyCF_ONLY_AST)
    v = SafetyVisitor()
    v.visit(astnode)
    return v.safe

def start_nodes(subdomain, clientobjectfile, numreplicas):
    print "[3] connecting to Planet Lab"
    # connect to PlanetLab
    numreplicas = int(numreplicas)
    connectedhosts = []
    while (numreplicas-len(connectedhosts) > 0):
        plconn = PLConnection()
        plconn.connect(numreplicas-len(connectedhosts))
        tmphosts = plconn.getHosts()
        print tmphosts
        for host in tmphosts:
            print "[4] uploading DNS tester"
            pathtodnstester = os.path.abspath("testdnsport.py")
            # upload testdnsport
            plconn.uploadone(host, pathtodnstester)
            print "[5] trying to bind to DNS port"
            dnssuccess = plconn.executecommandone(host, "sudo python testdnsport.py")
            if dnssuccess:
                print "DNS Port unavailable on %s" % host
                connectedhosts.append(host)
            else:
                plconn.executecommandone(host, "rm testdnsport.py")
    print connectedhosts
    # Now we have desired number of hosts at hand
    plconn = PLConnection(connectedhosts)
    os.system('make -q')
    pathtoconcoordbundle = os.path.abspath("concoord.tar.gz")
    pathtoshscript = os.path.abspath("plopenreplica.sh")
    plconn.uploadall(pathtoconcoordbundle)
    # upload shellscript
    plconn.uploadall(pathtoshscript)
    # initialize nodes
    print "[6] initializing"
    initsuccess,returnvalues = plconn.executecommandall("tar xzf concoord.tar.gz")
    if initsuccess:
        print "Initialization done!"

    # add nodes to open replica coordinator object
    openreplicacoordobj = OpenReplicaCoordProxy('128.84.60.206:6668,128.84.60.206:6669')
    print "Picked nodes: "
    for node in plconn.getHosts():
        openreplicacoordobj.addnodetosubdomain(subdomain, node+':7897')
        print node

def create_proxy(objectfile, classname):
    print "[7] creating proxy"
    modulename = os.path.basename(objectfile.name).rsplit(".")[0]
    proxyfile = createproxyfromname(modulename, classname)
    f = open(proxyfile.name, 'r')
    proxystring = f.read()
    f.close()
    print proxystring
    return proxystring

def main():
    # Create client object file
    if options.objectcode == None:
        objectfile = create_objectfilefromfile(options.objectfilename)
    else:
        objectfile = create_objectfilefromcode(options.objectfilename, options.objectcode)
    if not objectfile:
        print "Objectfile cannot be created. Check permissions."
        os._exit(0)
    # Check safety
    if not check_object(objectfile):
        os._exit(0)
    # Start Nodes
    start_nodes(options.subdomain, objectfile, options.replicanum)
    # Create Proxy
    clientproxy = create_proxy(objectfile, options.classname)
    
if __name__=='__main__':
    main()
