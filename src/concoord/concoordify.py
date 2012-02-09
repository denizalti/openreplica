'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Creates concoord objects
@date: August 1, 2011
@copyright: See COPYING.txt
'''
from optparse import OptionParser
from time import sleep,time
import os, sys, time, shutil
import ast, _ast
from safetychecker import *
from proxygenerator import *
from serversideproxyast import *

parser = OptionParser(usage="usage: %prog -f objectfilepath -c classname")
parser.add_option("-p", "--objectfilepath", action="store", dest="objectfilepath", help="client object file path")
parser.add_option("-n", "--classname", action="store", dest="classname", help="main class name")
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
        if not check_object(clientcode):
            print "Object is not safe for us to execute."
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
