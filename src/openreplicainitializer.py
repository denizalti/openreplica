'''
@author: deniz
@note: Initializes an OpenReplica instance
@date: November 18, 2011
'''
from optparse import OptionParser
from time import sleep,time
import os, sys, time, shutil
import ast, _ast
import subprocess
from plmanager import *
from safetychecker import *
from proxygenerator import *
from openreplicacoordobjproxy import *
from serversideproxyast import *

parser = OptionParser(usage="usage: %prog -s subdomain -n objectname -o objectcode -r replicas -a acceptors -n nameservers")
parser.add_option("-s", "--subdomain", action="store", dest="subdomain", help="name for the subdomain to reach openreplica")
parser.add_option("-f", "--objectfilepath", action="store", dest="objectfilepath", help="client object file path")
parser.add_option("-c", "--classname", action="store", dest="classname", help="main class name")
parser.add_option("-r", "--replicas", action="store", dest="replicanum", default=1, help="number of replicas")
parser.add_option("-a", "--acceptors", action="store", dest="acceptornum", default=1, help="number of acceptor")
parser.add_option("-n", "--nameservers", action="store", dest="nameservernum", default=1, help="number of nameservers")
(options, args) = parser.parse_args()

def check_object(clientobjectfilepath):
    print "-- checking object safety"
    astnode = compile(open(clientobjectfilepath, 'rU').read(),"<string>","exec",_ast.PyCF_ONLY_AST)
    v = SafetyVisitor()
    v.visit(astnode)
    return v.safe

# checks if a PL node is suitable for running a nameserver
def check_planetlab_dnsport(plconn, node):
    print "-- uploading DNS tester to ", node
    pathtodnstester = os.path.abspath("testdnsport.py")
    plconn.uploadone(node, pathtodnstester)
    print "-- trying to bind to DNS port"
    rtv, output = plconn.executecommandone(node, "sudo -A python testdnsport.py")
    if rtv:
        print "--- DNS Port available on %s" % node
    else:
        print "--- DNS Port unavailable on %s" % node
        plconn.executecommandone(node, "rm testdnsport.py")
    return rtv,output

def check_planetlab_pythonversion(plconn, node):
    print "-- Checking Python version on ", node
    command = 'python --version'
    rtv, output = plconn.executecommandone(node, command)
    if rtv:
        for out in output:
            if string.find(out, 'Python 2.7') >= 0:
                print "--- Python version acceptable!"
                return True,output
    print '\n'.join(output)
    return False,output

def start_nodes(subdomain, clientobjectfilepath, classname, configuration):
    # locate the right number of suitable PlanetLab nodes
    clientobjectfilename = os.path.basename(clientobjectfilepath)
    numreplicas, numacceptors, numnameservers = configuration
    bootstrap = PLConnection(1, [check_planetlab_pythonversion])
    nameservers = PLConnection(numnameservers, [check_planetlab_dnsport, check_planetlab_pythonversion])
    replicas = PLConnection(numreplicas-1, [check_planetlab_pythonversion])
    acceptors = PLConnection(numacceptors, [check_planetlab_pythonversion])
    print "Picked all nodes!"
    allnodes = PLConnection(nodes=nameservers.getHosts() + replicas.getHosts() + acceptors.getHosts() + bootstrap.getHosts())
    processnames = []
    ## Fix the server object
    fixedfile = editproxyfile(clientobjectfilepath, classname)
    allnodes.uploadall(fixedfile.name, "bin/"+clientobjectfilename)
    print "-- setting up the environment"
    print "--- initializing bootstrap"
    bootstrap.executecommandall("nohup python bin/replica.py -f %s -c %s" % (clientobjectfilename, classname), False)
    returnvalue = ('','')
    while returnvalue == ('',''):
        success, returnvalue = bootstrap.executecommandone(bootstrap.getHosts()[0], "ls | grep %s-descriptor" % clientobjectfilename[:-3])
    success,returnvalue = bootstrap.executecommandone(bootstrap.getHosts()[0], "cat %s-descriptor" % clientobjectfilename[:-3])
    bootstrapname = returnvalue[0]
    processnames.append(bootstrapname)
    print "Bootstrap: ", bootstrapname
    for acceptor in acceptors.getHosts():
        print "--- initializing acceptor on ", acceptor
        acceptors.executecommandone(acceptor, "nohup python bin/acceptor.py -b %s" % bootstrapname, False)
        #acceptors.executecommandall("nohup python bin/acceptor.py -b %s" % bootstrapname, False)
    if numreplicas-1 > 0:
        print "--- initializing replicas"
        replicas.executecommandall("nohup python bin/replica.py -f %s -c %s -b %s" % (clientobjectfilename, classname, bootstrapname), False)
        for replica in replicas.getHosts():
            processnames.append(get_node_name(replica, replicas, 'REPLICA'))
    if numnameservers > 0:
        print "--- initializing nameservers"
        nameservers.executecommandall("sudo -A nohup python bin/nameserver.py -n %s -f %s -c %s -b %s" % (subdomain, clientobjectfilename, classname, bootstrapname), False)
    print "Processes: ", processnames
    ## add the nameserver nodes to open replica coordinator object
    openreplicacoordobj = OpenReplicaCoordProxy('128.84.154.110:6668')
    print "Nodes: "
    for node in processnames:
        openreplicacoordobj.addnodetosubdomain(subdomain, node)
        print node
    return bootstrapname

def get_node_name(node, nodeconn, type):
    returnvalue = ('','')
    while returnvalue == ('',''):
        success, returnvalue = nodeconn.executecommandone(node, "ls | grep %s" % type)
    return returnvalue[0].strip().split('-')[1]

def create_proxy(clientobjectfilepath, classname, bootstrap=None):
    print "-- creating proxy"
    objectfilename = os.path.basename(clientobjectfilepath)
    if not objectfilename == clientobjectfilepath:
        shutil.copy(clientobjectfilepath, objectfilename)
    modulename = os.path.basename(objectfilename).rsplit(".")[0]
    proxyfile = createclientproxy(modulename, classname, bootstrap)
    f = open(proxyfile.name, 'r')
    proxystring = f.read()
    f.close()
    print proxystring
    return proxystring

def main():
    try:
        # Check safety
        if not check_object(options.objectfilepath):
            print "Object is not safe for us to execute."
            os._exit(1)
        # Start Nodes
        print "-- connecting to Planet Lab"
        configuration = (int(options.replicanum), int(options.acceptornum), int(options.nameservernum))
        start_nodes(options.subdomain, options.objectfilepath, options.classname, configuration)
        # Create Proxy
        clientproxy = create_proxy(options.objectfilepath, options.classname)
    except Exception as e:
        print "Error: "
        print e
    
if __name__=='__main__':
    main()
