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
from concoord.serversideproxyast import *
from concoord.openreplica.plmanager import *
from concoord.proxy.nameservercoord import *

parser = OptionParser(usage="usage: %prog -s subdomain -f objectfilepath -c classname -r replicas -a acceptors -n nameservers -o configpath")
parser.add_option("-s", "--subdomain", action="store", dest="subdomain", help="name for the subdomain to reach openreplica")
parser.add_option("-f", "--objectfilepath", action="store", dest="objectfilepath", help="client object file path")
parser.add_option("-c", "--classname", action="store", dest="classname", help="main class name")
parser.add_option("-r", "--replicas", action="store", dest="replicanum", default=1, help="number of replicas")
parser.add_option("-a", "--acceptors", action="store", dest="acceptornum", default=1, help="number of acceptor")
parser.add_option("-n", "--nameservers", action="store", dest="nameservernum", default=1, help="number of nameservers")
parser.add_option("-o", "--configpath", action="store", dest="configpath", default='', help="config file path")
(options, args) = parser.parse_args()

CONCOORDPATH = 'concoord/src/concoord/'

try:
    CONFIGDICT = load_configdict(options.configpath)
    NPYTHONPATH = CONFIGDICT['NPYTHONPATH']
    CONCOORD_HELPERDIR = CONFIGDICT['CONCOORD_HELPERDIR']
except:
    print "You need to set ssh credentials to use this script. Use -o option to provide configuration file path."
    NPYTHONPATH = 'python'

def check_object(clientcode):
    print "Checking object safety"
    astnode = compile(clientcode,"<string>","exec",_ast.PyCF_ONLY_AST)
    v = SafetyVisitor()
    v.visit(astnode)
    return v.safe

# checks if a PL node is suitable for running a nameserver
def check_planetlab_dnsport(plconn, node):
    print "Uploading DNS tester to ", node
    pathtodnstester = CONCOORD_HELPERDIR+'testdnsport.py'
    plconn.uploadone(node, pathtodnstester)
    print "Trying to bind to DNS port"
    rtv, output = plconn.executecommandone(node, "sudo " + NPYTHONPATH + " testdnsport.py")
    if rtv:
        print "DNS Port available on %s" % node
    else:
        print "DNS Port not available on %s" % node
        plconn.executecommandone(node, "rm testdnsport.py")
    return rtv,output

def check_planetlab_pythonversion(plconn, node):
    print "Uploading Python version tester to ", node
    pathtopvtester = CONCOORD_HELPERDIR+'testpythonversion.py' 
    plconn.uploadone(node, pathtopvtester)
    print "Checking Python version"
    rtv, output = plconn.executecommandone(node, NPYTHONPATH + " testpythonversion.py")
    if rtv:
        print "Python version acceptable on %s" % node
    else:
        print "Python version not acceptable on %s" % node
        plconn.executecommandone(node, "rm testpythonversion.py")
    return rtv,output

def kill_node(node, uniqueid):
    addr,port = node.split(':')
    cmd = 'ps auxww | sed -e \'s/[ ][^ ]*$//\' | grep pytho[n] | grep '+uniqueid+' | grep '+port+' | awk \'{print $2}\' | sudo -A xargs kill -9'
    try:
        nodeconn = PLConnection(nodes=[addr], configdict=CONFIGDICT)
        reply = nodeconn.executecommandone(addr, cmd)
        return reply
    except:
        return CONFIGDICT

def start_nodes(subdomain, clientobjectfilepath, classname, configuration):
    # locate the right number of suitable PlanetLab nodes
    clientobjectfilename = os.path.basename(clientobjectfilepath)
    numreplicas, numacceptors, numnameservers = configuration
    if numreplicas < 1 or numacceptors < 1 or numnameservers < 1:
        print "Invalid configuration:"
        print "The configuration requires at least 1 Replica, 1 Acceptor and 1 Nameserver"
        os._exit()
    bootstrap = PLConnection(1, [check_planetlab_pythonversion], configdict=CONFIGDICT)
    nameservers = PLConnection(numnameservers, [check_planetlab_pythonversion], configdict=CONFIGDICT)
    replicas = PLConnection(numreplicas-1, [check_planetlab_pythonversion], configdict=CONFIGDICT)
    acceptors = PLConnection(numacceptors, [check_planetlab_pythonversion], configdict=CONFIGDICT)
    allnodes = PLConnection(nodes=nameservers.getHosts() + replicas.getHosts() + acceptors.getHosts() + bootstrap.getHosts(), configdict=CONFIGDICT)
    print "=== Picked Nodes ==="
    for node in allnodes.getHosts():
        print node
    processnames = []
    ## Fix the server object
    print "Fixing object file for use on the server side.."
    fixedfile = editproxyfile(clientobjectfilepath, classname)
    print "Uploading object file to replicas.."
    allnodes.uploadall(fixedfile.name, CONCOORDPATH + clientobjectfilename)
    print "--> Setting up the environment..."
    # BOOTSTRAP
    print "--- Bootstrap Replica ---"
    port = random.randint(14000, 15000)
    p = bootstrap.executecommandone(bootstrap.getHosts()[0], "nohup "+ NPYTHONPATH + " " + CONCOORDPATH + "replica.py -a %s -p %d -f %s -c %s >> /tmp/test 2>&1 &" % (bootstrap.getHosts()[0], port, clientobjectfilename, classname), False)
    while terminated(p):
        port = random.randint(14000, 15000)
        p = bootstrap.executecommandone(bootstrap.getHosts()[0], "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "replica.py -a %s -p %d -f %s -c %s >> /tmp/test 2>&1 &" % (bootstrap.getHosts()[0], port, clientobjectfilename, classname), False)
    bootstrapname = bootstrap.getHosts()[0]+':'+str(port)
    processnames.append((NODE_REPLICA, bootstrapname))
    print bootstrapname
    # ACCEPTORS
    print "--- Acceptors ---"
    for acceptor in acceptors.getHosts():
        port = random.randint(14000, 15000)
        p = acceptors.executecommandone(acceptor, "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "acceptor.py -a %s -p %d -f %s -b %s >> /tmp/test 2>&1 &" % (acceptor, port, clientobjectfilename, bootstrapname), False)
        while terminated(p):
            port = random.randint(14000, 15000)
            p = acceptors.executecommandone(acceptor, "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "acceptor.py -a %s -p %d -f %s -b %s >> /tmp/test 2>&1 &" % (acceptor, port, clientobjectfilename, bootstrapname), False)
        acceptorname = acceptor+':'+str(port)
        processnames.append((NODE_ACCEPTOR, acceptorname))
        print acceptorname
    # REPLICAS
    if numreplicas-1 > 0:
        print "--- Replicas ---"
    for replica in replicas.getHosts():
        port = random.randint(14000, 15000)
        p = replicas.executecommandone(replica, "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "replica.py -a %s -p %d -f %s -c %s -b %s >> /tmp/%s 2>&1 &" % (replica, port, clientobjectfilename, classname, bootstrapname, clientobjectfilename), False)
        while terminated(p):
            port = random.randint(14000, 15000)
            p = replicas.executecommandone(replica, "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "replica.py -a %s -p %d -f %s -c %s -b %s >> /tmp/%s 2>&1 &" % (replica, port, clientobjectfilename, classname, bootstrapname, clientobjectfilename), False)
        replicaname = replica+':'+str(port)
        processnames.append((NODE_REPLICA, replicaname))
        print replicaname
    # NAMESERVERS
    print "--- Nameservers ---"
    servicetype = NS_SLAVE
    master = 'openreplica.org'
    for nameserver in nameservers.getHosts():
        port = random.randint(14000, 15000)
        p = nameservers.executecommandone(nameserver, "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "nameserver.py -n %s -a %s -p %d -f %s -c %s -b %s -t %d -m %s >> /tmp/%s 2>&1 &" % (subdomain, nameserver, port, clientobjectfilename, classname, bootstrapname, servicetype, master, clientobjectfilename), False)
        while terminated(p):
            port = random.randint(14000, 15000)
            p = nameservers.executecommandone(nameserver, "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "nameserver.py -n %s -a %s -p %d -f %s -c %s -b %s -t %d -m %s >> /tmp/%s 2>&1 &" % (subdomain, nameserver, port, clientobjectfilename, classname, bootstrapname, servicetype, master, clientobjectfilename), False)
        nameservername = nameserver+':'+str(port)
        processnames.append((NODE_NAMESERVER, nameservername))
        print nameservername
    print "All clear!"
    ## add the nameserver nodes to open replica coordinator object
    nameservercoordobj = NameserverCoord('openreplica.org')
    print "Adding nodes to OpenReplica Nameserver Coordination Object:"
    for nodetype,node in processnames:
        print "- ",  node_names[nodetype] , "| ", node
        nameservercoordobj.addnodetosubdomain(subdomain, nodetype, node)
    return bootstrapname

def terminated(p):
    i = 5
    done = p.poll() is not None
    while not done and i>0: # Not terminated yet
        sleep(1)
        i -= 1
        done = p.poll() is not None
    return done

def main():
    with open(options.objectfilepath, 'rU') as fd:
        clientcode = fd.read()
        # Check safety
    if not check_object(clientcode):
        print "Object is not safe for us to execute."
        os._exit(1)
        # Start Nodes
    print "Connecting to Planet Lab"
    configuration = (int(options.replicanum), int(options.acceptornum), int(options.nameservernum))
    start_nodes(options.subdomain, options.objectfilepath, options.classname, configuration)
        # Create Proxy
    print "Creating proxy..."
    clientproxycode = createclientproxy(clientcode, options.classname, None)
    clientproxycode = clientproxycode.replace('\n\n\n', '\n\n')
    print "Proxy Code:"
    print clientproxycode
    
if __name__=='__main__':
    main()
