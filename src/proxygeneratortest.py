import inspect, types
import os, shutil
from optparse import OptionParser
from proxygenerator import *

parser = OptionParser(usage="usage: %prog -m modulename -o objectname")
parser.add_option("-m", "--modulename", action="store", dest="modulename", help="name for the module (filename)")
parser.add_option("-o", "--objectname", action="store", dest="objectname", help="name for the object (class definition name)")
(options, args) = parser.parse_args()

moduleobject = __import__(options.modulename, globals(), locals(), [], -1)
classobject = getattr(moduleobject, options.objectname)
create_file(classobject, options.modulename)
