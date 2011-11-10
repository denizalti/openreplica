'''
@author: denizalti
@note: initializer for openreplica
@date: October 1, 2011
'''
import os
from optparse import OptionParser
from safetychecker import *

parser = OptionParser(usage="usage: %prog -s subdomain -n objectname -o objectcode -r replicas")
parser.add_option("-s", "--subdomain", action="store", dest="subdomain", help="name for the subdomain to reach openreplica")
parser.add_option("-n", "--objectname", action="store", dest="objectname", help="client object name")
parser.add_option("-o", "--objectcode", action="store", dest="objectcode", help="client object code")
parser.add_option("-r", "--replicas", action="store", dest="replicanum", default=1, help="number of replicas")
(options, args) = parser.parse_args()

def main():
    objectfile = create_object(options.objectname, options.objectcode)
    objectsafe = check_object(objectfile)
    if not objectsafe:
        print "Object not safe. Terminating.."
        return
    start_system(objectname)
    clientproxy = create_proxy()
    return clientproxy

def create_object(objectname, objectcode):
    print "creating object.."
    try:
        abspath = os.path.abspath(objectname)
        objectfile = open(abspath, "w")
        objectfile.write(objectcode)
        objectfile.close()
        return True
    except:
        return False

def check_object(objectfile):
    print "checking object safety.."
    astnode = compile(open(objectfile.name, 'rU').read(),"<string>","exec",_ast.PyCF_ONLY_AST)
    v = Visitor()
    v.visit(astnode)
    return True

def start_system(objectname):
    print "starting system.."
    
def create_proxy(objectname):
    print "creating proxy.."
    proxyfile = createproxyfromname(objectname)
    f = open(proxyfile.name, 'r')
    proxystring = f.read()
    return proxystring

if __name__=='__main__':
    main()
