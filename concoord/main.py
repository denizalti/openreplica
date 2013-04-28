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
concoord [object $objectfilepath $classname] - concoordifies a python object"

def start_node(nodetype):
    nodename = node_names[nodetype].lower()
    node = getattr(__import__('concoord.'+nodename, globals(), locals(), -1), nodename.capitalize())()
    node.startservice()
    signal.signal(signal.SIGINT, node.terminate_handler)
    signal.signal(signal.SIGTERM, node.terminate_handler)
    signal.pause()

def check_object(clientcode):
    astnode = compile(clientcode,"<string>","exec",_ast.PyCF_ONLY_AST)
    v = SafetyVisitor()
    v.visit(astnode)
    return v.safe

def concoordify():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--objectname", action="store", dest="objectname", default='',
                        help="client object dotted name module.Class")
    parser.add_argument("-t", "--token", action="store", dest="securitytoken", default=None,
                        help="security token")
    parser.add_argument("-p", "--proxytype", action="store", dest="proxytype", type=int, default=0,
                        help="0:BASIC, 1:BLOCKING, 2:CLIENT-SIDE BATCHING, 3: SERVER-SIDE BATCHING ")
    parser.add_argument("-s", "--safe", action="store_true", dest="safe", default=False,
                        help="safety checking on/off")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", default=None,
                        help="verbose mode on/off")
    args = parser.parse_args()

    if not args.objectname:
        print parser.print_help()
        return
    import importlib
    objectloc,a,classname = args.objectname.rpartition('.')
    object = None
    try:
        module = importlib.import_module(objectloc)
        if hasattr(module, classname):
            object = getattr(module, classname)()
    except (ValueError, ImportError, AttributeError):
        print "Can't find module %s, check your PYTHONPATH." % objectloc

    if module.__file__.endswith('pyc'):
        filename = module.__file__[:-1]
    else:
        filename = module.__file__
    with open(filename, 'rU') as fd:
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
    clientproxycode = createclientproxy(clientcode, classname, args.securitytoken, args.proxytype)
    clientproxycode = clientproxycode.replace('\n\n\n', '\n\n')
    proxyfile = open(filename[:-3]+"proxy.py", 'w')
    proxyfile.write(clientproxycode)
    proxyfile.close()
    print "Client proxy file created with name: ", proxyfile.name


def main():
    if len(sys.argv) < 2:
        print HELPSTR
        sys.exit()

    eventtype = sys.argv[1].upper()
    sys.argv.pop(1)
    if eventtype == node_names[NODE_ACCEPTOR]:
        start_node(NODE_ACCEPTOR)
    elif eventtype == node_names[NODE_REPLICA]:
        start_node(NODE_REPLICA)
    elif eventtype == node_names[NODE_NAMESERVER]:
        start_node(NODE_NAMESERVER)
    elif eventtype == 'ADDNODE':
        add_node()
    elif eventtype == 'INITIALIZE':
        initialize()
    elif eventtype == 'OBJECT':
        concoordify()
    else:
        print HELPSTR

if __name__=='__main__':
    main()
