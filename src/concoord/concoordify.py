'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Creates concoord objects
@copyright: See LICENSE
'''
from optparse import OptionParser
from time import sleep,time
import os, sys, time, shutil
import ast, _ast
from concoord.safetychecker import *
from concoord.proxygenerator import *
from concoord.serversideproxyast import *

parser = OptionParser(usage="usage: %prog -f objectfilepath -c classname -s safe")
parser.add_option("-f", "--objectfilepath", action="store", dest="objectfilepath", help="client object file path")
parser.add_option("-c", "--classname", action="store", dest="classname", help="main class name")
parser.add_option("-s", "--safe", action="store_true", dest="safe", default=False, help="safety checking on/off")
(options, args) = parser.parse_args()

def check_object(clientcode):
    print "Checking object safety"
    astnode = compile(clientcode,"<string>","exec",_ast.PyCF_ONLY_AST)
    v = SafetyVisitor()
    v.visit(astnode)
    return v.safe

def main():
    try:
        with open(options.objectfilepath, 'rU') as fd:
            clientcode = fd.read()
        if options.safe:
            if not check_object(clientcode):
                print "Object is not safe to execute."
                os._exit(1)
        fixedfile = editproxyfile(options.objectfilepath, options.classname)
        print "Fixed server-side object: ", fixedfile.name
        clientproxycode = createclientproxy(clientcode, options.classname, None)
        clientproxycode = clientproxycode.replace('\n\n\n', '\n\n')
        proxyfile = open(options.objectfilepath+"proxy", 'w')
        proxyfile.write(clientproxycode)
        proxyfile.close()
        print "Client proxy: ", proxyfile.name
    except Exception as e:
        print "Error: ", e
    
if __name__=='__main__':
    main()
