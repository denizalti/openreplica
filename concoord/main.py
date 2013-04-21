#!/usr/bin/env python
'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: concoord script
@date: January 20, 2012
@copyright: See LICENSE
'''
import argparse
import signal
from time import sleep,time
import os, sys, time, shutil
import ast, _ast
from concoord.enums import *
from concoord.safetychecker import *
from concoord.proxygenerator import *

HELPSTR = "concoord, version 1.0.0-release:\n\
concoord [acceptor] - starts an acceptor node\n\
concoord [replica] - starts a replica node\n\
concoord [nameserver] - starts a nameserver node\n\
concoord [addnode] - adds nodes to a specified concoord instance\n\
concoord [initialize] - initializes a concoord instance with given number of nodes\n\
concoord [object $objectfilepath $classname] - concoordifies a python object"

def start_node(nodetype):
    parser = argparse.ArgumentParser()
    parser.add_argument("REPLICA")
    parser.add_argument("-a", "--addr", action="store", dest="addr",
                        help="addr for the node")
    parser.add_argument("-p", "--port", action="store", dest="port", type=int,
                        help="port for the node")
    parser.add_argument("-b", "--boot", action="store", dest="bootstrap",
                        help="address:port:type triple for the bootstrap peer")
    parser.add_argument("-o", "--objectname", action="store", dest="objectname", default='',
                        help="client object dotted name")
    parser.add_argument("-l", "--logger", action="store", dest="logger", default='',
                        help="logger address")
    parser.add_argument("-c", "--configpath", action="store", dest="configpath", default='',
                        help="config file path")
    parser.add_argument("-n", "--name", action="store", dest="domain", default='',
                        help="domainname that the nameserver will accept queries for")
    parser.add_argument("-t", "--type", action="store", dest="type", default='',
                        help="1: Master Nameserver 2: Slave Nameserver (requires a Master) 3:Route53 (requires a Route53 zone)")
    parser.add_argument("-m", "--master", action="store", dest="master", default='',
                        help="ipaddr:port for the master nameserver")
    parser.add_argument("-d", "--debug", action="store_true", dest="debug", default=False,
                        help="debug on/off")
    args = parser.parse_args()
    nodename = node_names[nodetype].lower()
    node = getattr(__import__('concoord.'+nodename, globals(), locals(), -1), nodename.capitalize())()
    node.startservice()
    signal.signal(signal.SIGINT, node.terminate_handler)
    signal.signal(signal.SIGTERM, node.terminate_handler)
    signal.pause()

def add_node():
    from concoord.openreplica.openreplicaaddnode import parser, args, start_node
    try:
        start_node(args.nodetype, args.subdomain, args.objectfilepath,
                   args.classname, args.bootstrapname)
    except Exception as e:
        parser.print_help()

def initialize():
    from concoord.openreplica.openreplicainitializer import parser, args, start_nodes, check_object
    try:
        with open(args.objectfilepath, 'rU') as fd:
            clientcode = fd.read()
        # Check safety
        if not check_object(clientcode):
            print "Object is not safe for us to execute."
            os._exit(1)
        # Start Nodes
        configuration = (int(args.replicanum), int(args.acceptornum), int(args.nameservernum))
        start_nodes(args.subdomain, args.objectfilepath, args.classname, configuration)
        # Create Proxy
        print "Creating proxy..."
        clientproxycode = createclientproxy(clientcode, args.classname, None)
        clientproxycode = clientproxycode.replace('\n\n\n', '\n\n')
        print "Proxy Code:"
        print clientproxycode
    except Exception as e:
        parser.print_help()

def check_object(clientcode):
    astnode = compile(clientcode,"<string>","exec",_ast.PyCF_ONLY_AST)
    v = SafetyVisitor()
    v.visit(astnode)
    return v.safe

def concoordify():
    parser = argparse.ArgumentParser()
    parser.add_argument("OBJECT")
    parser.add_argument("-f", "--objectfilepath", action="store", dest="objectfilepath",
                        help="client object file path")
    parser.add_argument("-c", "--classname", action="store", dest="classname",
                        help="main class name")
    parser.add_argument("-s", "--safe", action="store_true", dest="safe", default=False,
                        help="safety checking on/off")
    parser.add_argument("-t", "--token", action="store", dest="securitytoken", default=None,
                        help="security token")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", default=None,
                        help="verbose option")
    args = parser.parse_args()

    with open(args.objectfilepath, 'rU') as fd:
        clientcode = fd.read()
    if args.safe:
        if args.verbose:
            print "Checking object safety"
        if not check_object(clientcode):
            print "Object is not safe to execute."
            os._exit(1)
        elif args.verbose:
            print "Object is safe!"
    if args.verbose:
        print "Creating clientproxy"
    clientproxycode = createclientproxy(clientcode, args.classname,
                                        args.securitytoken)
    clientproxycode = clientproxycode.replace('\n\n\n', '\n\n')
    proxyfile = open(args.objectfilepath+"proxy", 'w')
    proxyfile.write(clientproxycode)
    proxyfile.close()
    print "Client proxy file created with name: ", proxyfile.name


def main():
    if len(sys.argv) < 2:
        print HELPSTR
        sys.exit()
        
    sys.argv[1] = sys.argv[1].upper()
    if sys.argv[1] == node_names[NODE_ACCEPTOR]:
        start_node(NODE_ACCEPTOR)
    elif sys.argv[1] == node_names[NODE_REPLICA]:
        start_node(NODE_REPLICA)
    elif sys.argv[1] == node_names[NODE_NAMESERVER]:
        start_node(NODE_NAMESERVER)
    elif sys.argv[1] == 'ADDNODE':
        add_node()
    elif sys.argv[1] == 'INITIALIZE':
        initialize()
    elif sys.argv[1] == 'OBJECT':
        concoordify()
    else:
        print HELPSTR

if __name__=='__main__':
    main()
