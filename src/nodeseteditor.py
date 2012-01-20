'''
@author: deniz
@note: Adds and removes specific nodes from the node set
@date: January 20, 2012
'''
from time import sleep,time
import os, sys, time, shutil
import subprocess
from enums import *
from plmanager import *
from serversideproxyast import *
from openreplicainitializer import *
from openreplicacoordobjproxy import *

def get_startup_cmd(nodetype, subdomain, node, port, clientobjectfilename, classname, bootstrapname):
    if nodetype == NODE_REPLICA:
        startupcmd = "nohup python bin/replica.py -a %s -p %d -f %s -c %s -b %s" % (node, port, clientobjectfilename, classname, bootstrapname)
    elif nodetype == NODE_ACCEPTOR:
        startupcmd = "nohup python bin/acceptor.py -a %s -p %d -f %s -b %s" % (node, port, clientobjectfilename, bootstrapname)
    elif nodetype == NODE_NAMESERVER:
        startupcmd =  "sudo -A nohup python bin/nameserver.py -n %s -a %s -p %d -f %s -c %s -b %s" % (subdomain+'.openreplica.org', node, port, clientobjectfilename, classname, bootstrapname)
    return startupcmd
        
def start_node(nodetype, subdomain, clientobjectfilepath, classname, bootstrapname):
    clientobjectfilename = os.path.basename(clientobjectfilepath)
    if nodetype == NODE_NAMESERVER:
        nodeconn = PLConnection(1, [check_planetlab_dnsport, check_planetlab_pythonversion])
    else:
        nodeconn = PLConnection(1, [check_planetlab_pythonversion])
    print "-- Picked Node: %s" % nodeconn.getHosts()[0]
    fixedfile = editproxyfile(clientobjectfilepath, classname)
    nodeconn.uploadall(fixedfile.name, "bin/"+clientobjectfilename)
    for node in nodeconn.getHosts():
        port = random.randint(14000, 15000)
        p = nodeconn.executecommandone(node, get_startup_cmd(nodetype, subdomain, node, port, clientobjectfilename, classname, bootstrapname), False)
        while terminated(p):
            port = random.randint(14000, 15000)
            p = nodeconn.executecommandone(node, get_startup_cmd(nodetype, subdomain, node, port, clientobjectfilename, classname, bootstrapname), False)
        nodename = node+':'+str(port)
        print nodename
    # Add it to the object if it is a nameserver
    if nodetype == NODE_NAMESERVER:
        openreplicacoordobj = OpenReplicaCoordProxy('128.84.154.110:6668')
        openreplicacoordobj.addnodetosubdomain(subdomain, node)

def terminated(p):
    i = 5
    done = p.poll() is not None
    while not done and i>0: # Not terminated yet
        sleep(1)
        i -= 1
        done = p.poll() is not None
    return done
