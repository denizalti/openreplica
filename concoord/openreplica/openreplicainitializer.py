'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Initializes an OpenReplica instance
@copyright: See LICENSE
'''
import argparse
import ast, _ast
import os, sys
from concoord.enums import *
from concoord.utils import *
from concoord.safetychecker import *
from concoord.proxygenerator import *
from concoord.openreplica.plmanager import *
from concoord.proxy.nameservercoord import *

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--subdomain", action="store", dest="subdomain", help="name for the subdomain to reach openreplica")
parser.add_argument("-f", "--objectfilepath", action="store", dest="objectfilepath", help="client object file path")
parser.add_argument("-c", "--classname", action="store", dest="classname", help="main class name")
parser.add_argument("-r", "--replicas", action="store", dest="replicanum", default=1, help="number of replicas")
parser.add_argument("-a", "--acceptors", action="store", dest="acceptornum", default=1, help="number of acceptor")
parser.add_argument("-n", "--nameservers", action="store", dest="nameservernum", default=1, help="number of nameservers")
parser.add_argument("-o", "--configpath", action="store", dest="configpath", default='', help="config file path")
parser.add_argument("-t", "--token", action="store", dest="token", default='', help="unique security token")
args = parser.parse_args()

DEBUG = False
NODE_BOOTSTRAP = 5
STDOUT, STDERR = range(2)

try:
    CONFIGDICT = load_configdict(args.configpath)
    NPYTHONPATH = CONFIGDICT['NPYTHONPATH']
    CONCOORD_HELPERDIR = CONFIGDICT['CONCOORD_HELPERDIR']
    CONCOORDPATH = CONFIGDICT['CONCOORDPATH']
    LOGGERNODE = CONFIGDICT['LOGGERNODE']
except:
    print "You need to set ssh credentials to use this script. Use -o option to provide configuration file path."
    NPYTHONPATH = 'python'

def check_object(clientcode):
    print ("Checking object for security issues..."),
    astnode = compile(clientcode,"<string>","exec",_ast.PyCF_ONLY_AST)
    v = SafetyVisitor()
    v.visit(astnode)
    return v.safe

# checks if a PL node is suitable for running a nameserver
def check_planetlab_dnsport(plconn, node):
    pathtodnstester = CONCOORD_HELPERDIR+'testdnsport.py'
    plconn.uploadone(node, pathtodnstester)
    terminated, output = plconn.executecommandone(node, "sudo "+NPYTHONPATH+" testdnsport.py")
    success = terminated and output[STDERR] == ''
    plconn.executecommandone(node, "rm testdnsport.py")
    return success,output

def check_planetlab_pythonversion(plconn, node):
    pathtopvtester = CONCOORD_HELPERDIR+'testpythonversion.py'
    plconn.uploadone(node, pathtopvtester)
    terminated, output = plconn.executecommandone(node, NPYTHONPATH + " testpythonversion.py")
    success = terminated and output[STDERR] == ''
    plconn.executecommandone(node, "rm testpythonversion.py")
    return success,output

def kill_node(node, uniqueid):
    addr,port = node.split(':')
    cmd = 'ps auxww | sed -e \'s/[ ][^ ]*$//\' | grep pytho[n] | grep '+uniqueid+' | grep '+port+' | awk \'{print $2}\' | sudo -A xargs kill -9'
    try:
        nodeconn = PLConnection(nodes=[addr], configdict=CONFIGDICT)
        reply = nodeconn.executecommandone(addr, cmd)
        return reply
    except:
        return CONFIGDICT

def get_startup_cmd(nodetype, node, port, clientobjectfilename, classname='', bootstrapname='', subdomain='', servicetype=None, master=''):
    startupcmd = ''
    if nodetype == NODE_BOOTSTRAP:
        startupcmd = "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "replica.py -a %s -p %d -f %s -c %s -l %s > foo.out 2> foo.err < /dev/null &" % (node, port, clientobjectfilename, classname, LOGGERNODE)
    elif nodetype == NODE_REPLICA:
        startupcmd = "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "replica.py -a %s -p %d -f %s -c %s -b %s -l %s > foo.out 2> foo.err < /dev/null &" % (node, port, clientobjectfilename, classname, bootstrapname, LOGGERNODE)
    elif nodetype == NODE_ACCEPTOR:
        startupcmd = "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "acceptor.py -a %s -p %d -f %s -b %s -l %s > foo.out 2> foo.err < /dev/null &" % (node, port, clientobjectfilename, bootstrapname, LOGGERNODE)
    elif nodetype == NODE_NAMESERVER:
        startupcmd =  "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "nameserver.py -n %s -a %s -p %d -f %s -c %s -b %s -t %d -m %s -l %s > foo.out 2> foo.err < /dev/null &" % (subdomain+'.openreplica.org', node, port, clientobjectfilename, classname, bootstrapname, servicetype, master, LOGGERNODE)
    return startupcmd

def start_nodes(subdomain, clientobjectfilepath, classname, configuration, token):
    # Prepare data necessary for starting nodes
    clientobjectfilename = os.path.basename(clientobjectfilepath)
    numreplicas, numacceptors, numnameservers = configuration
    if numreplicas < 1 or numacceptors < 1 or numnameservers < 1:
        print "Invalid configuration:"
        print "The configuration requires at least 1 Replica, 1 Acceptor and 1 Nameserver"
        print "Please try again."
        os._exit()
    processnames = []

    success = False
    # locate the PlanetLab node for bootstrap, check the node, upload object and start the node
    while not success:
        try:
            bootstrap = PLConnection(1, [check_planetlab_pythonversion], configdict=CONFIGDICT)
            print "Trying node: %s" % bootstrap.getHosts()[0]
            success = bootstrap.uploadall(clientobjectfilepath, CONCOORDPATH + clientobjectfilename)
        except:
            success = False
        if not success:
            continue
        # Object upload is done.
        port = random.randint(14000, 15000)
        node = bootstrap.getHosts()[0]
        p = bootstrap.executecommandone(node, get_startup_cmd(NODE_BOOTSTRAP, node, port, clientobjectfilename, classname), False)
        terminated, output = bootstrap.executecommandone(node, 'cat foo.out')
        terminated = terminated and output[STDOUT] != ''
        bootstrap.executecommandone(node, 'rm foo*')
        numtries = 0
        while terminated and numtries < 5:
            print "Failed to start node, trying again.."
            port = random.randint(14000, 15000)
            p = bootstrap.executecommandone(node, get_startup_cmd(NODE_BOOTSTRAP, node, port, clientobjectfilename, classname), False)
            terminated, output = bootstrap.executecommandone(node, 'cat foo.out')
            terminated = terminated and output[STDOUT] != ''
            bootstrap.executecommandone(node, 'rm foo*')
            numtries += 1
        if numtries == 5:
            success = False
            continue
        # Bootstrap is started
        bootstrapname = bootstrap.getHosts()[0]+':'+str(port)
        processnames.append((NODE_REPLICA, bootstrapname))
        print "Replica #0 is started: %s" % bootstrapname

    # locate the PlanetLab node for replicas, check the nodes, upload object and start the nodes
    for i in range(numreplicas-1):
        success = False
        while not success:
            try:
                replica = PLConnection(1, [check_planetlab_pythonversion], configdict=CONFIGDICT)
                print "Trying node: %s" % replica.getHosts()[0]
                success = replica.uploadall(clientobjectfilepath, CONCOORDPATH + clientobjectfilename)
            except:
                success = False
            if not success:
                continue
            # Object upload is done.
            port = random.randint(14000, 15000)
            node = replica.getHosts()[0]
            p = replica.executecommandone(replica.getHosts()[0], get_startup_cmd(NODE_REPLICA, node, port, clientobjectfilename, classname, bootstrapname), False)
            terminated, output = replica.executecommandone(node, 'cat foo.out')
            terminated = terminated and output[STDOUT] != ''
            replica.executecommandone(node, 'rm foo*')
            numtries = 0
            while terminated and numtries < 5:
                port = random.randint(14000, 15000)
                p = replica.executecommandone(replica.getHosts()[0], get_startup_cmd(NODE_REPLICA, node, port, clientobjectfilename, classname, bootstrapname), False)
                terminated, output = replica.executecommandone(node, 'cat foo.out')
                terminated = terminated and output[STDOUT] != ''
                replica.executecommandone(node, 'rm foo*')
                numtries += 1
            if numtries == 5:
                success = False
                continue
            # Replica is started
            replicaname = replica.getHosts()[0]+':'+str(port)
            processnames.append((NODE_REPLICA, replicaname))
            print "Replica #%d is started: %s" % (i+1, replicaname)

    # locate the PlanetLab node for acceptors, check the nodes, upload object and start the nodes
    for i in range(numacceptors):
        success = False
        while not success:
            try:
                acceptor = PLConnection(1, [check_planetlab_pythonversion], configdict=CONFIGDICT)
                print "Trying node: %s"% acceptor.getHosts()[0]
                success = acceptor.uploadall(clientobjectfilepath, CONCOORDPATH + clientobjectfilename)
            except:
                success = False
            if not success:
                continue
            # Object upload is done.
            port = random.randint(14000, 15000)
            node = acceptor.getHosts()[0]
            p = acceptor.executecommandone(acceptor.getHosts()[0], get_startup_cmd(NODE_ACCEPTOR, node, port, clientobjectfilename, bootstrapname=bootstrapname), False)
            terminated, output = acceptor.executecommandone(node, 'cat foo.out')
            terminated = terminated and output[STDOUT] != ''
            acceptor.executecommandone(node, 'rm foo*')
            numtries = 0
            while terminated and numtries < 5:
                port = random.randint(14000, 15000)
                p = acceptor.executecommandone(acceptor.getHosts()[0], get_startup_cmd(NODE_ACCEPTOR, node, port, clientobjectfilename, bootstrapname=bootstrapname), False)
                terminated, output = acceptor.executecommandone(node, 'cat foo.out')
                terminated = terminated and output[STDOUT] != ''
                acceptor.executecommandone(node, 'rm foo*')
                numtries += 1
            if numtries == 5:
                success = False
                continue
            # Acceptor is started
            acceptorname = acceptor.getHosts()[0]+':'+str(port)
            processnames.append((NODE_ACCEPTOR, acceptorname))
            print "Acceptor #%d is started: %s" % (i, acceptorname)

    servicetype = NS_SLAVE
    master = 'openreplica.org'
    # locate the PlanetLab node for nameservers, check the nodes, upload object and start the nodes
    for i in range(numnameservers):
        success = False
        while not success:
            try:
                nameserver = PLConnection(1, [check_planetlab_pythonversion], configdict=CONFIGDICT)
                print "Trying node: %s"% nameserver.getHosts()[0]
                success = nameserver.uploadall(clientobjectfilepath, CONCOORDPATH + clientobjectfilename)
            except:
                success = False
            if not success:
                continue
            # Object upload is done.
            port = random.randint(14000, 15000)
            node = nameserver.getHosts()[0]
            p = nameserver.executecommandone(nameserver.getHosts()[0], get_startup_cmd(NODE_NAMESERVER, node, port, clientobjectfilename, classname, bootstrapname, subdomain, servicetype, master), False)
            terminated, output = nameserver.executecommandone(node, 'cat foo.out')
            terminated = terminated and output[STDOUT] != ''
            nameserver.executecommandone(node, 'rm foo*')
            numtries = 0
            while terminated and numtries < 5:
                port = random.randint(14000, 15000)
                p = nameserver.executecommandone(nameserver.getHosts()[0], get_startup_cmd(NODE_NAMESERVER, node, port, clientobjectfilename, classname, bootstrapname, subdomain, servicetype, master), False)
                terminated, output = nameserver.executecommandone(node, 'cat foo.out')
                terminated = terminated and output[STDOUT] != ''
                nameserver.executecommandone(node, 'rm foo*')
                numtries += 1
            if numtries == 5:
                success = False
                continue
            # Nameserver is started
            nameservername = nameserver.getHosts()[0]+':'+str(port)
            processnames.append((NODE_NAMESERVER, nameservername))
            print "Nameserver #%d is started: %s" % (i, nameservername)

    ## add nodes to OpenReplica coordinator object
    nameservercoordobj = NameserverCoord('openreplica.org')
    for nodetype,node in processnames:
        nameservercoordobj.addnodetosubdomain(subdomain, nodetype, node)
    # All nodes are started
    print "All nodes have been started!"
    return bootstrapname

def main():
    with open(args.objectfilepath, 'rU') as fd:
        clientcode = fd.read()
        # Check safety
    if not check_object(clientcode):
        print "Object is not safe for us to execute."
        print "If you would like to use this object, use ConCoord to deploy it."
        os._exit(1)
        # Start Nodes
    print " [PASSED]"
    configuration = (int(args.replicanum), int(args.acceptornum), int(args.nameservernum))
    print "Starting nodes..."
    start_nodes(args.subdomain, args.objectfilepath, args.classname, configuration, args.token)
    # Create Proxy
    print "Creating proxy..."
    clientproxycode = createclientproxy(clientcode, args.classname, args.token)
    clientproxycode = clientproxycode.replace('\n\n\n', '\n\n')
    print "Proxy Code:"
    print clientproxycode
    print 'DONE'
    return 0

if __name__=='__main__':
    main()
