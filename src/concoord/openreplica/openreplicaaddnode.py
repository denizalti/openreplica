'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Adds nodes to an OpenReplica instance
@copyright: See LICENSE
'''
import subprocess
import os, sys, time, shutil
from time import sleep,time
from optparse import OptionParser
from concoord.enums import *
from concoord.utils import *
from concoord.openreplica.plmanager import *
from concoord.proxy.nameservercoord import *

parser = OptionParser(usage="usage: %prog -t nodetype -s subdomain -f objectpath -c classname -b bootstrap")
parser.add_option("-t", "--nodetype", action="store", dest="nodetype", help="node type")
parser.add_option("-s", "--subdomain", action="store", dest="subdomain", help="name for the subdomain to reach openreplica")
parser.add_option("-f", "--objectfilepath", action="store", dest="objectfilepath", help="client object file path")
parser.add_option("-c", "--classname", action="store", dest="classname", help="main class name")
parser.add_option("-o", "--configpath", action="store", dest="configpath", default='', help="config file path")
parser.add_option("-b", "--bootstrap", action="store", dest="bootstrapname", help="bootstrap name")
(options, args) = parser.parse_args()

CONCOORDPATH = 'concoord/src/concoord/'
try:
    CONFIGDICT = load_configdict(options.configpath)
    NPYTHONPATH = CONFIGDICT['NPYTHONPATH']
    CONCOORD_HELPERDIR = CONFIGDICT['CONCOORD_HELPERDIR']
    LOGGERNODE = CONFIGDICT['LOGGERNODE']
except:
    NPYTHONPATH = 'python'

def terminated(p):
    i = 5
    done = p.poll() is not None
    while not done and i>0:
        sleep(1)
        i -= 1
        done = p.poll() is not None
    return done

# checks if a PL node is suitable for running a nameserver
def check_planetlab_dnsport(plconn, node):
    print "Uploading DNS tester to ", node
    pathtodnstester = CONCOORD_HELPERDIR+'testdnsport.py'
    plconn.uploadone(node, pathtodnstester)
    print "Trying to bind to DNS port"
    rtv, output = plconn.executecommandone(node, "sudo "+NPYTHONPATH+" testdnsport.py")
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
    rtv, output = plconn.executecommandone(node, NPYTHONPATH+" testpythonversion.py")
    if rtv:
        print "Python version acceptable on %s" % node
    else:
        print "Python version not acceptable on %s" % node
        plconn.executecommandone(node, "rm testpythonversion.py")
    return rtv,output

def get_startup_cmd(nodetype, subdomain, node, port, clientobjectfilename, classname, bootstrapname):
    startupcmd = ''
    if nodetype == NODE_REPLICA:
        startupcmd = "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "replica.py -a %s -p %d -f %s -c %s -b %s -l %s" % (node, port, clientobjectfilename, classname, bootstrapname, LOGGERNODE)
    elif nodetype == NODE_ACCEPTOR:
        startupcmd = "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "acceptor.py -a %s -p %d -f %s -b %s -l %s" % (node, port, clientobjectfilename, bootstrapname, LOGGERNODE)
    elif nodetype == NODE_NAMESERVER:
        startupcmd =  "nohup " + NPYTHONPATH + " " + CONCOORDPATH + "nameserver.py -n %s -a %s -p %d -f %s -c %s -b %s -t %d -m %s -l %s" % (subdomain+'.openreplica.org', node, port, clientobjectfilename, classname, bootstrapname, servicetype, master, LOGGERNODE)
    return startupcmd
        
def start_node(nodetype, subdomain, clientobjectfilepath, classname, bootstrapname):
    nodetype = int(nodetype)
    servicetype = NS_SLAVE
    master = 'openreplica.org'
    print "==== Adding %s ====" % node_names[nodetype]
    clientobjectfilename = os.path.basename(clientobjectfilepath)
    if nodetype == NODE_NAMESERVER:
        nodeconn = PLConnection(1, [check_planetlab_dnsport, check_planetlab_pythonversion], configdict=CONFIGDICT)
    else:
        nodeconn = PLConnection(1, [check_planetlab_pythonversion], configdict=CONFIGDICT)
    print "Picked Node: %s" % nodeconn.getHosts()[0]
    print "Connecting to bootstrap: %s" % bootstrapname
    if nodetype != NODE_ACCEPTOR:
        nodeconn.uploadall(clientobjectfilepath+"fixed", CONCOORDPATH+clientobjectfilename)
    for node in nodeconn.getHosts():
        port = random.randint(14000, 15000)
        p = nodeconn.executecommandone(node, get_startup_cmd(nodetype, subdomain, node, port,
                                                             clientobjectfilename, classname,
                                                             bootstrapname, servicetype, master), False)
        while terminated(p):
            port = random.randint(14000, 15000)
            print get_startup_cmd(nodetype, subdomain, node, port,clientobjectfilename, classname, bootstrapname, servicetype, master)
            p = nodeconn.executecommandone(node, get_startup_cmd(nodetype, subdomain, node, port,
                                                                 clientobjectfilename, classname,
                                                                 bootstrapname, servicetype, master), False)
            print p
        nodename = node+':'+str(port)
        print "Node is started: %s" % nodename
    # Add it to the object if it is a nameserver
    nameservercoordobj = NameserverCoord('openreplica.org')
    print "Adding node to OpenReplica Nameserver Coordination Object:"
    print "- ",  node_names[nodetype] , "| ", nodename
    nameservercoordobj.addnodetosubdomain(subdomain, nodetype, nodename)

def main():
#    try:
    print "Connecting to Planet Lab"
    start_node(options.nodetype, options.subdomain, options.objectfilepath,
               options.classname, options.bootstrapname)
#    except Exception as e:
#        parser.print_help()
    
if __name__=='__main__':
    main()
