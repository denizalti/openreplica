'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Adds nodes to an OpenReplica instance
@copyright: See LICENSE
'''
import argparse
import os, sys, time
from concoord.enums import *
from concoord.utils import *
from concoord.openreplica.plmanager import *
from concoord.proxy.nameservercoord import *

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--nodetype", action="store", dest="nodetype", help="node type")
parser.add_argument("-s", "--subdomain", action="store", dest="subdomain", help="name for the subdomain to reach openreplica")
parser.add_argument("-f", "--objectfilepath", action="store", dest="objectfilepath", help="client object file path")
parser.add_argument("-c", "--classname", action="store", dest="classname", help="main class name")
parser.add_argument("-o", "--configpath", action="store", dest="configpath", default='', help="config file path")
parser.add_argument("-b", "--bootstrap", action="store", dest="bootstrapname", help="bootstrap name")
args = parser.parse_args()

STDOUT, STDERR = range(2)

try:
    CONFIGDICT = load_configdict(args.configpath)
    NPYTHONPATH = CONFIGDICT['NPYTHONPATH']
    CONCOORD_HELPERDIR = CONFIGDICT['CONCOORD_HELPERDIR']
    LOGGERNODE = CONFIGDICT['LOGGERNODE']
    CONCOORDPATH = CONFIGDICT['CONCOORDPATH']
except:
    NPYTHONPATH = 'python'

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

def get_startup_cmd(nodetype, subdomain, node, port, clientobjectfilename, classname, bootstrapname, servicetype, master):
    startupcmd = ''
    if nodetype == NODE_REPLICA:
        startupcmd = "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "replica.py -a %s -p %d -f %s -c %s -b %s -l %s > foo.out 2> foo.err < /dev/null &" % (node, port, clientobjectfilename, classname, bootstrapname, LOGGERNODE)
    elif nodetype == NODE_ACCEPTOR:
        startupcmd = "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "acceptor.py -a %s -p %d -f %s -b %s -l %s > foo.out 2> foo.err < /dev/null &" % (node, port, clientobjectfilename, bootstrapname, LOGGERNODE)
    elif nodetype == NODE_NAMESERVER:
        startupcmd =  "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "nameserver.py -n %s -a %s -p %d -f %s -c %s -b %s -t %d -m %s -l %s > foo.out 2> foo.err < /dev/null &" % (subdomain+'.openreplica.org', node, port, clientobjectfilename, classname, bootstrapname, servicetype, master, LOGGERNODE)
    return startupcmd

def start_node(nodetype, subdomain, clientobjectfilepath, classname, bootstrapname):
    nodetype = int(nodetype)
    servicetype = NS_SLAVE
    master = 'openreplica.org'
    print "\n==== Adding %s ====" % node_names[nodetype]
    clientobjectfilename = os.path.basename(clientobjectfilepath)
    print "Picking node..."
    if nodetype == NODE_NAMESERVER:
        nodeconn = PLConnection(1, [check_planetlab_dnsport, check_planetlab_pythonversion], configdict=CONFIGDICT)
    else:
        nodeconn = PLConnection(1, [check_planetlab_pythonversion], configdict=CONFIGDICT)
    node = nodeconn.getHosts()[0]
    print "Picked Node: %s" % node

    terminated = True
    numtries = 0
    while terminated and numtries < 5:
        if nodetype != NODE_ACCEPTOR:
            nodeconn.uploadall(clientobjectfilepath, CONCOORDPATH + clientobjectfilename)
        port = random.randint(14000, 15000)
        p = nodeconn.executecommandone(node, get_startup_cmd(nodetype, subdomain, node, port,
                                                             clientobjectfilename, classname,
                                                             bootstrapname, servicetype, master), False)
        terminated, output = nodeconn.executecommandone(node, 'cat foo.out')
        terminated = terminated and output[STDOUT] != ''
        nodeconn.executecommandone(node, 'rm foo*')
        nodename = node + ':' + str(port)
        numtries += 1

    if terminated:
        print "Adding node FAILED. Please try again."
        return

    # Add it to the object if it is a nameserver
    nameservercoordobj = NameserverCoord('openreplica.org')
    nameservercoordobj.addnodetosubdomain(subdomain, nodetype, nodename)
    # node is started
    print "Node is started: %s" % nodename

def main():
    start_node(args.nodetype, args.subdomain, args.objectfilepath,
               args.classname, args.bootstrapname)
    print 'DONE'

if __name__=='__main__':
    main()
