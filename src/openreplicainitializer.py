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

parser = OptionParser(usage="usage: %prog -s subdomain -n objectname -o objectcode -r replicas -a acceptors -n nameservers")
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
def check_planetlab_dnsport(plconn, node):
    print "[5.1] uploading DNS tester to ", node
    pathtodnstester = os.path.abspath("testdnsport.py")
    plconn.uploadone(node, pathtodnstester)
    print "[5.2] trying to bind to DNS port"
    rtv, output = plconn.executecommandone(node, "sudo python testdnsport.py")
    if rtv:
        print "[5.3] DNS Port available on %s" % node
    else:
        print "[5.3] DNS Port unavailable on %s" % node
        plconn.executecommandone(node, "rm testdnsport.py")
    return rtv,output

def check_planetlab_pythonversion(plconn, node):
    print "[6.1] Checking Python version on ", node
    command = 'python --version'
    rtv, output = plconn.executecommandone(node, command)
    if rtv:
        for out in output:
            if string.find(out, 'Python 2.7') >= 0:
                print "[6.2] Python version acceptable!"
                return True,output
    print "[6.3] Python version not acceptable!"
    return False,output

def start_nodes(subdomain, clientobjectfile, configuration):
    # locate the right number of suitable PlanetLab nodes
    numreplicas, numacceptors, numnameservers = configuration
    bootstrap = PLConnection(1, [check_planetlab_pythonversion])
    nameservers = PLConnection(numnameservers, [check_planetlab_dnsport, check_planetlab_pythonversion])
    replicas = PLConnection(numreplicas-1, [check_planetlab_pythonversion])
    acceptors = PLConnection(numacceptors, [check_planetlab_pythonversion])
    print "Done!"
    allnodes = PLConnection(nodes=nameservers.getHosts() + replicas.getHosts() + acceptors.getHosts() + bootstrap.getHosts())
    processnames = []
    os.system('make')
    pathtoconcoordbundle = os.path.abspath("concoord.tar.gz")
    print "[7] uploading data"
    allnodes.uploadall(pathtoconcoordbundle)
    allnodes.executecommandall("tar xzf concoord.tar.gz")
    print "[8.1] initializing bootstrap"
    bootstrap.executecommandall("python replica.py -o bank.Bank", False)
    returnvalue = ('','')
    while returnvalue == ('',''):
        success, returnvalue = bootstrap.executecommandone(bootstrap.getHosts()[0], "ls | grep REPLICA")
        print success, returnvalue
    bootstrapname = returnvalue[0].strip().split('-')[1]
    processnames.append(bootstrapname)
    print "Bootstrap: ", bootstrapname
    print "[8.2] initializing acceptors"
    acceptors.executecommandall("python acceptor.py -b %s" % bootstrapname, False)
    for acceptor in acceptors.getHosts():
        returnvalue = ('','')
        while returnvalue == ('',''):
            success, returnvalue = bootstrap.executecommandone(acceptor, "ls | grep ACCEPTOR")
            print success, returnvalue
        processnames.append(returnvalue[0].strip().split('-')[1])
    print processnames
    nameservers.executecommandall("")
    replicas.executecommandall("")
    print "Initialization done!"
    # add the nameserver nodes to open replica coordinator object
    openreplicacoordobj = OpenReplicaCoordProxy('128.84.60.206:6668,128.84.60.206:6669')
    print "Picked nodes: "
    for node in processnames:
        openreplicacoordobj.addnodetosubdomain(subdomain, node)
        print node

def create_proxy(objectfile, classname):
    print "[9] creating proxy"
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
