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

parser = OptionParser(usage="usage: %prog -s subdomain -f objectfilepath -c classname -r replicas -a acceptors -n nameservers -o configpath -t token")
parser.add_option("-s", "--subdomain", action="store", dest="subdomain", help="name for the subdomain to reach openreplica")
parser.add_option("-f", "--objectfilepath", action="store", dest="objectfilepath", help="client object file path")
parser.add_option("-c", "--classname", action="store", dest="classname", help="main class name")
parser.add_option("-r", "--replicas", action="store", dest="replicanum", default=1, help="number of replicas")
parser.add_option("-a", "--acceptors", action="store", dest="acceptornum", default=1, help="number of acceptor")
parser.add_option("-n", "--nameservers", action="store", dest="nameservernum", default=1, help="number of nameservers")
parser.add_option("-o", "--configpath", action="store", dest="configpath", default='', help="config file path")
parser.add_option("-t", "--token", action="store", dest="token", default='', help="unique security token")
(options, args) = parser.parse_args()

NODE_BOOTSTRAP = 5
CONCOORDPATH = 'concoord-0.3.0/concoord/'

try:
    CONFIGDICT = load_configdict(options.configpath)
    NPYTHONPATH = CONFIGDICT['NPYTHONPATH']
    CONCOORD_HELPERDIR = CONFIGDICT['CONCOORD_HELPERDIR']
    LOGGERNODE = CONFIGDICT['LOGGERNODE']
except:
    print "You need to set ssh credentials to use this script. Use -o option to provide configuration file path."
    NPYTHONPATH = 'python'

def check_object(clientcode):
    print "Checking object safety"
    astnode = compile(clientcode,"<string>","exec",_ast.PyCF_ONLY_AST)
    v = SafetyVisitor()
    v.visit(astnode)
    return v.safe

def check_planetlab_pythonversion(plconn, node):
    pathtopvtester = CONCOORD_HELPERDIR+'testpythonversion.py' 
    plconn.uploadone(node, pathtopvtester)
    rtv, output = plconn.executecommandone(node, NPYTHONPATH + " testpythonversion.py")
    if not rtv:
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

def get_startup_cmd(nodetype, node, port, clientobjectfilename, classname='', bootstrapname='', subdomain='', servicetype=None, master=''):
    startupcmd = ''
    if nodetype == NODE_BOOTSTRAP:
        startupcmd = "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "replica.py -a %s -p %d -f %s -c %s -l %s" % (node, port, clientobjectfilename, classname, LOGGERNODE)
    elif nodetype == NODE_REPLICA:
        startupcmd = "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "replica.py -a %s -p %d -f %s -c %s -b %s -l %s" % (node, port, clientobjectfilename, classname, bootstrapname, LOGGERNODE)
    elif nodetype == NODE_ACCEPTOR:
        startupcmd = "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "acceptor.py -a %s -p %d -f %s -b %s -l %s" % (node, port, clientobjectfilename, bootstrapname, LOGGERNODE)
    elif nodetype == NODE_NAMESERVER:
        startupcmd =  "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "nameserver.py -n %s -a %s -p %d -f %s -c %s -b %s -t %d -m %s -l %s" % (subdomain+'.openreplica.org', node, port, clientobjectfilename, classname, bootstrapname, servicetype, master, LOGGERNODE)
    return startupcmd

def start_nodes(subdomain, clientobjectfilepath, classname, configuration, token):
    # Prepare data necessary for starting nodes
    clientobjectfilename = os.path.basename(clientobjectfilepath)
    numreplicas, numacceptors, numnameservers = configuration
    if numreplicas < 1 or numacceptors < 1 or numnameservers < 1:
        print "Invalid configuration:"
        print "The configuration requires at least 1 Replica, 1 Acceptor and 1 Nameserver"
        os._exit()
    processnames = []

    success = False
    # locate the PlanetLab node for bootstrap, check the node, upload object and start the node
    while not success:
#        try:
        bootstrap = PLConnection(1, [check_planetlab_pythonversion], configdict=CONFIGDICT)
        print "Trying node: %s" % bootstrap.getHosts()[0]
        success = bootstrap.uploadall(clientobjectfilename, CONCOORDPATH + clientobjectfilename)
#        except:
#            success = False
        if not success:
            continue
        # Object upload is done.
        port = random.randint(14000, 15000)
        node = bootstrap.getHosts()[0]
        p = bootstrap.executecommandone(node, get_startup_cmd(NODE_BOOTSTRAP, node, port, clientobjectfilename, classname), False)
        numtries = 0
        while terminated(p) and numtries < 5:
            port = random.randint(14000, 15000)
            p = bootstrap.executecommandone(node, get_startup_cmd(NODE_BOOTSTRAP, node, port, clientobjectfilename, classname), False)
            numtries += 1
        if numtries == 5:
            success = False
            continue
        # Bootstrap is started
        bootstrapname = bootstrap.getHosts()[0]+':'+str(port)
        processnames.append((NODE_REPLICA, bootstrapname))
        print "Bootstrap is started: %s" % bootstrapname

    # locate the PlanetLab node for replicas, check the nodes, upload object and start the nodes
    for i in range(numreplicas-1):
        success = False
        while not success:
            try:
                replica = PLConnection(1, [check_planetlab_pythonversion], configdict=CONFIGDICT)
                print "Trying node: %s"% replica.getHosts()[0]
                success = replica.uploadall(clientobjectfilename, CONCOORDPATH + clientobjectfilename)
            except:
                success = False
            if not success:
                continue
            # Object upload is done.
            port = random.randint(14000, 15000)
            node = replica.getHosts()[0]
            p = replica.executecommandone(replica.getHosts()[0], get_startup_cmd(NODE_REPLICA, node, port, clientobjectfilename, classname, bootstrapname), False)
            numtries = 0
            while terminated(p) and numtries < 5:
                port = random.randint(14000, 15000)
                p = replica.executecommandone(replica.getHosts()[0], get_startup_cmd(NODE_REPLICA, node, port, clientobjectfilename, classname, bootstrapname), False)
                numtries += 1
            if numtries == 5:
                success = False
                continue
            # Replica is started
            replicaname = replica.getHosts()[0]+':'+str(port)
            processnames.append((NODE_REPLICA, replicaname))
            print "Replica #%d is started: %s" % (i, replicaname)
    
    # locate the PlanetLab node for acceptors, check the nodes, upload object and start the nodes
    for i in range(numacceptors):
        success = False
        while not success:
            try:
                acceptor = PLConnection(1, [check_planetlab_pythonversion], configdict=CONFIGDICT)
                print "Trying node: %s"% acceptor.getHosts()[0]
                success = acceptor.uploadall(clientobjectfilename, CONCOORDPATH + clientobjectfilename)
            except:
                success = False
            if not success:
                continue
            # Object upload is done.
            port = random.randint(14000, 15000)
            node = acceptor.getHosts()[0]
            p = acceptor.executecommandone(acceptor.getHosts()[0], get_startup_cmd(NODE_ACCEPTOR, node, port, clientobjectfilename, bootstrapname=bootstrapname), False)
            numtries = 0
            while terminated(p) and numtries < 5:
                port = random.randint(14000, 15000)
                p = acceptor.executecommandone(acceptor.getHosts()[0], get_startup_cmd(NODE_ACCEPTOR, node, port, clientobjectfilename, bootstrapname=bootstrapname), False)
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
                success = nameserver.uploadall(clientobjectfilename, CONCOORDPATH + clientobjectfilename)
            except:
                success = False
            if not success:
                continue
            # Object upload is done.
            port = random.randint(14000, 15000)
            node = nameserver.getHosts()[0]
            p = nameserver.executecommandone(nameserver.getHosts()[0], get_startup_cmd(NODE_NAMESERVER, node, port, clientobjectfilename, classname, bootstrapname, subdomain, servicetype, master), False)
            numtries = 0
            while terminated(p) and numtries < 5:
                port = random.randint(14000, 15000)
                p = nameserver.executecommandone(nameserver.getHosts()[0], get_startup_cmd(NODE_NAMESERVER, node, port, clientobjectfilename, classname, bootstrapname, subdomain, servicetype, master), False)
                numtries += 1
            if numtries == 5:
                success = False
                continue
            # Nameserver is started
            nameservername = nameserver.getHosts()[0]+':'+str(port)
            processnames.append((NODE_NAMESERVER, nameservername))
            print "Name server #%d is started: %s" % (i, nameservername)

    # All nodes are started
    print "All clear!"
    ## add nodes to OpenReplica coordinator object
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
    start_nodes(options.subdomain, options.objectfilepath, options.classname, configuration, options.token)
        # Create Proxy
    print "Creating proxy..."
    clientproxycode = createclientproxy(clientcode, options.classname, options.token, None)
    clientproxycode = clientproxycode.replace('\n\n\n', '\n\n')
    print "Proxy Code:"
    print clientproxycode
    
if __name__=='__main__':
    main()
