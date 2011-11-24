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
parser.add_option("-f", "--objectfilename", action="store", dest="objectfilename", help="client object file name")
parser.add_option("-c", "--classname", action="store", dest="classname", help="main class name")
parser.add_option("-o", "--objectcode", action="store", dest="objectcode", help="client object code")
parser.add_option("-r", "--replicas", action="store", dest="replicanum", default=1, help="number of replicas")
parser.add_option("-a", "--acceptors", action="store", dest="acceptornum", default=1, help="number of acceptor")
parser.add_option("-n", "--nameservers", action="store", dest="nameservernum", default=1, help="number of nameservers")
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

# checks if a PL node is suitable for running a nameserver
def check_planetlab_nameserver_node(node):
    print "[5.1] uploading DNS tester to ", node
    pathtodnstester = os.path.abspath("testdnsport.py")
    plconn.uploadone(node, pathtodnstester)
    print "[5.2] trying to bind to DNS port"
    dnssuccess = plconn.executecommandone(node, "sudo python testdnsport.py")
    if dnssuccess:
        print "[5.3] DNS Port available on %s" % node
    else:
        print "[5.3] DNS Port unavailable on %s" % node
        plconn.executecommandone(node, "rm testdnsport.py")
    return dnssuccess

def start_nodes(subdomain, clientobjectfile, configuration):
    # locate the right number of suitable PlanetLab nodes
    numreplicas, numacceptors, numnameservers = configuration
    nameservers = PLConnection(numnameservers, check_planetlab_nameserver_node)
    replicas = PLConnection(numreplicas)
    acceptors = PLConnection(numacceptors)
    all = PLConnection(nodes=nameservers.getHosts() + replicas.getHosts() + acceptors.getHosts())

    os.system('make -q')
    pathtoconcoordbundle = os.path.abspath("concoord.tar.gz")
    pathtoshscript = os.path.abspath("plopenreplica.sh")
    print "[6] uploading data"
    all.uploadall(pathtoconcoordbundle)
    all.uploadall(pathtoshscript)
    print "[7] initializing"
    all.executecommandall("tar xzf concoord.tar.gz")

    acceptors.executecommandall("python acceptor.py")
    nameservers.executecommandall("")
    replicas.executecommandall("")
    print "Initialization done!"

    # add the nameserver nodes to open replica coordinator object
    openreplicacoordobj = OpenReplicaCoordProxy('128.84.60.206:6668,128.84.60.206:6669')
    print "Picked nodes: "
    for node in nameserver.getHosts():
        openreplicacoordobj.addnodetosubdomain(subdomain, node)
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
    print "[3] connecting to Planet Lab"
    configuration = (int(options.replicanum), int(options.acceptornum), int(options.nameservernum))
    start_nodes(options.subdomain, objectfile, configuration)
    # Create Proxy
    clientproxy = create_proxy(objectfile, options.classname)
    
if __name__=='__main__':
    main()
