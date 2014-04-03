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
import concoord
from concoord.enums import *
from concoord.safetychecker import *
from concoord.proxygenerator import *
import ConfigParser

HELPSTR = "concoord, version 1.1.0-release:\n\
concoord replica [-a address -p port -o objectname -b bootstrap -l loggeraddress -w writetodisk -d debug -n domainname -r route53] - starts a replica\n\
concoord route53id [aws_access_key_id] - adds AWS_ACCESS_KEY_ID to route53 CONFIG file\n\
concoord route53key [aws_secret_access_key] - adds AWS_SECRET_ACCESS_KEY to route53 CONFIG file\n\
concoord object [objectfilepath classname] - concoordifies a python object"

ROUTE53CONFIGFILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'route53.cfg')
config = ConfigParser.RawConfigParser()

## ROUTE53

def touch_config_file():
    with open(ROUTE53CONFIGFILE, 'a'):
        os.utime(ROUTE53CONFIGFILE, None)

def read_config_file():
    config.read(ROUTE53CONFIGFILE)
    section = 'ENVIRONMENT'
    options = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
    rewritten = True
    if not config.has_section(section):
        rewritten = True
        config.add_section(section)
    for option in options:
        if not config.has_option(section, option):
            rewritten = True
            config.set(section, option, '')
    if rewritten:
        # Write to CONFIG file
        with open(ROUTE53CONFIGFILE, 'wb') as configfile:
            config.write(configfile)
        config.read(ROUTE53CONFIGFILE)
    awsid = config.get('ENVIRONMENT', 'AWS_ACCESS_KEY_ID')
    awskey = config.get('ENVIRONMENT', 'AWS_SECRET_ACCESS_KEY')
    return (awsid,awskey)

def print_config_file():
    print "AWS_ACCESS_KEY_ID= %s\nAWS_SECRET_ACCESS_KEY= %s" % read_config_file()

def add_id_to_config(newid):
    awsid,awskey = read_config_file()
    if awsid and awsid == newid:
        print "AWS_ACCESS_KEY_ID is already in the CONFIG file."
        return
    # Write to CONFIG file
    config.set('ENVIRONMENT', 'AWS_ACCESS_KEY_ID', newid)
    with open(ROUTE53CONFIGFILE, 'wb') as configfile:
        config.write(configfile)

def add_key_to_config(newkey):
    awsid,awskey = read_config_file()
    if awskey and awskey == newkey:
        print "AWS_SECRET_ACCESS_KEY is already in the CONFIG file."
        return
    # Write to CONFIG file
    config.set('ENVIRONMENT', 'AWS_SECRET_ACCESS_KEY', newkey)
    with open(ROUTE53CONFIGFILE, 'wb') as configfile:
        config.write(configfile)

## REPLICA

def start_replica():
    node = getattr(__import__('concoord.replica', globals(), locals(), -1), 'Replica')()
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
    if eventtype == 'REPLICA':
        start_replica()
    elif eventtype == 'ROUTE53ID':
        print "Adding AWS_ACCESS_KEY_ID to CONFIG:", sys.argv[1]
        add_id_to_config(sys.argv[1])
    elif eventtype == 'ROUTE53KEY':
        print "Adding AWS_SECRET_ACCESS_KEY to CONFIG:", sys.argv[1]
        add_key_to_config(sys.argv[1])
    elif eventtype == 'INITIALIZE':
        initialize()
    elif eventtype == 'OBJECT':
        concoordify()
    else:
        print HELPSTR

if __name__=='__main__':
    main()
