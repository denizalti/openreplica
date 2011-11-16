'''
@author: denizalti
@note: initializer for openreplica
@date: October 1, 2011
'''
import os
from optparse import OptionParser
from safetychecker import *
from initializer import *
from proxygenerator import *

parser = OptionParser(usage="usage: %prog -s subdomain -n objectname -o objectcode -r replicas")
parser.add_option("-s", "--subdomain", action="store", dest="subdomain", help="name for the subdomain to reach openreplica")
parser.add_option("-n", "--objectfilename", action="store", dest="objectfilename", help="client object file name")
parser.add_option("-o", "--objectcode", action="store", dest="objectcode", help="client object code")
parser.add_option("-r", "--replicas", action="store", dest="replicanum", default=1, help="number of replicas")
(options, args) = parser.parse_args()

def create_objectfile(objectfilename, objectcode):
    print "creating object.."
    try:
        abspath = os.path.abspath(objectfilename)
        objectfile = open(abspath, "w")
        objectfile.write(objectcode)
        objectfile.close()
        return objectfile
    except:
        return None

def check_object(objectfile):
    print "checking object safety.."
    astnode = compile(open(objectfile.name, 'rU').read(),"<string>","exec",_ast.PyCF_ONLY_AST)
    v = SafetyVisitor()
    v.visit(astnode)
    return v.safe

def start_system(subdomain, objectfile, replicanum):
    print "starting system.."
    i = Initializer()
    i.start_concoord(subdomain, objectfile, replicanum)
    
def create_proxy(objectfile):
    print "creating proxy.."
    proxyfile = createproxyfromname(objectname)
    f = open(proxyfile.name, 'r')
    proxystring = f.read()
    return proxystring

def main():
    objectfile = create_objectfile(options.objectfilename, options.objectcode)
    if objectfile:
        print "Objectfile cannot be created. Check permissions."
        os._exit(0)
    if not check_object(objectfile):
        os._exit(0)
    start_system(options.subdomain, objectfile, options.replicanum)
    clientproxy = create_proxy(objectfile)
    return clientproxy

if __name__=='__main__':
    main()
