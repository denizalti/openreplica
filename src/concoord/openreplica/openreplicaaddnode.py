'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Adds nodes to an OpenReplica instance
@date: January 20, 2012
@copyright: See COPYING.txt
'''
from optparse import OptionParser
from time import sleep,time
import os, sys, time, shutil
import subprocess
from enums import *
from plmanager import *
from openreplicacoordobjproxy import *

parser = OptionParser(usage="usage: %prog -t nodetype -s subdomain -p objectpath -n classname -b bootstrap")
parser.add_option("-t", "--nodetype", action="store", dest="nodetype", help="node type")
parser.add_option("-s", "--subdomain", action="store", dest="subdomain", help="name for the subdomain to reach openreplica")
parser.add_option("-p", "--objectpath", action="store", dest="clientobjectfilepath", help="client object file path")
parser.add_option("-n", "--classname", action="store", dest="classname", help="main class name")
parser.add_option("-b", "--bootstrap", action="store", dest="bootstrapname", help="bootstrap name")
(options, args) = parser.parse_args()

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
    pathtodnstester = os.path.abspath("testdnsport.py")
    plconn.uploadone(node, pathtodnstester)
    print "Trying to bind to DNS port"
    rtv, output = plconn.executecommandone(node, "sudo -A /home/cornell_openreplica/python2.7/bin/python2.7 testdnsport.py")
    if rtv:
        print "DNS Port available on %s" % node
    else:
        print "DNS Port not available on %s" % node
        plconn.executecommandone(node, "rm testdnsport.py")
    return rtv,output

def check_planetlab_pythonversion(plconn, node):
    print "Checking Python version on ", node
    command = '/home/cornell_openreplica/python2.7/bin/python2.7 --version'
    rtv, output = plconn.executecommandone(node, command)
    if rtv:
        for out in output:
            if string.find(out, 'Python 2.7') >= 0:
                print "Python version acceptable!"
                return True,output
    print '\n'.join(output)
    return False,output

def get_startup_cmd(nodetype, subdomain, node, port, clientobjectfilename, classname, bootstrapname):
    startupcmd = ''
    if nodetype == NODE_REPLICA:
        startupcmd = "nohup /home/cornell_openreplica/python2.7/bin/python2.7 bin/replica.py -a %s -p %d -f %s -c %s -b %s" % (node, port, clientobjectfilename, classname, bootstrapname)
    elif nodetype == NODE_ACCEPTOR:
        startupcmd = "nohup /home/cornell_openreplica/python2.7/bin/python2.7 bin/acceptor.py -a %s -p %d -f %s -b %s" % (node, port, clientobjectfilename, bootstrapname)
    elif nodetype == NODE_NAMESERVER:
        startupcmd =  "sudo -A nohup /home/cornell_openreplica/python2.7/bin/python2.7 bin/nameserver.py -n %s -a %s -p %d -f %s -c %s -b %s" % (subdomain+'.openreplica.org', node, port, clientobjectfilename, classname, bootstrapname)
    return startupcmd
        
def start_node(nodetype, subdomain, clientobjectfilepath, classname, bootstrapname):
    nodetype = int(nodetype)
    print "==== Adding %s ====" % node_names[nodetype]
    clientobjectfilename = os.path.basename(clientobjectfilepath)
    if nodetype == NODE_NAMESERVER:
        nodeconn = PLConnection(1, [check_planetlab_dnsport, check_planetlab_pythonversion])
    else:
        nodeconn = PLConnection(1, [check_planetlab_pythonversion])
    print "Picked Node: %s" % nodeconn.getHosts()[0]
    print "Connecting to bootstrap: %s" % bootstrapname
    if nodetype != NODE_ACCEPTOR:
        nodeconn.uploadall(clientobjectfilepath+"fixed", "bin/"+clientobjectfilename)
    for node in nodeconn.getHosts():
        port = random.randint(14000, 15000)
        p = nodeconn.executecommandone(node, get_startup_cmd(nodetype, subdomain, node, port,
                                                             clientobjectfilename, classname,
                                                             bootstrapname), False)
        while terminated(p):
            port = random.randint(14000, 15000)
            p = nodeconn.executecommandone(node, get_startup_cmd(nodetype, subdomain, node, port,
                                                                 clientobjectfilename, classname,
                                                                 bootstrapname), False)
            print p
        nodename = node+':'+str(port)
        print "Node is started: %s" % nodename
    # Add it to the object if it is a nameserver
    if nodetype == NODE_NAMESERVER:
        print "Adding Nameserver to the subdomain Coordination Object" 
        openreplicacoordobj = OpenReplicaCoordProxy('128.84.154.110:6668')
        openreplicacoordobj.addnodetosubdomain(subdomain, node)

def main():
    try:
        print "Connecting to Planet Lab"
        start_node(options.nodetype, options.subdomain, options.clientobjectfilepath,
                   options.classname, options.bootstrapname)
    except Exception as e:
        print "Error: ", e
    
if __name__=='__main__':
    main()
