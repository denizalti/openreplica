from proxygenerator import *
from optparse import OptionParser

parser = OptionParser(usage="usage: %prog -o --obj objectname")
parser.add_option("-o", "--obj", action="store", dest="objectname", help="name of the object to be converted to a proxy")
(options, args) = parser.parse_args()

moduleobject = get_class(options.objectname)
classobject = getattr(moduleobject, options.objectname.capitalize())
create_file(classobject)
