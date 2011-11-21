import inspect, types, string
import os, shutil
from optparse import OptionParser

parser = OptionParser(usage="usage: %prog -m modulename -o objectname")
parser.add_option("-m", "--modulename", action="store", dest="modulename", help="name for the module (filename)")
parser.add_option("-o", "--objectname", action="store", dest="objectname", help="name for the object (class definition name)")
(options, args) = parser.parse_args()

def get_functions_of_obj(classobj):
    templist = dir(classobj)
    dirlist = []
    for temp in templist:
        if isinstance(classobj.__dict__[temp], types.FunctionType):
            dirlist.append(temp)
    return dirlist

def get_arguments_of_func(function):
    args, _, _, values = inspect.getargspec(function)
    return args

def editfile(classobj, modulename):
    abspath = os.path.abspath(modulename+'.py')
    objectfile = open(abspath, 'r')
    filecontent = ''
    for line in objectfile:
        filecontent += line
    objectfile.close()
    objectfuncs = get_functions_of_obj(classobj)
    for func in objectfuncs:
        olddef = "def " + func + "(" + ", ".join(get_arguments_of_func(getattr(classobj, func))) + "):"
        print olddef
        newdef = "def " + func + "(" + ", ".join(get_arguments_of_func(getattr(classobj, func))) + ", **kwargs):"
        filecontent = string.replace(filecontent, olddef, newdef, 1)
    objectfile = open(abspath, 'w')
    objectfile.write(filecontent)
    objectfile.close()
    
get_module = lambda x: globals()[x]

def createproxyfromname(modulename, classname):
    moduleobject = __import__(modulename, globals(), locals(), [], -1)
    classobject = getattr(moduleobject, classname)
    return create_file(classobject,modulename)

def getobjectfromname(modulename, classname):
    moduleobject = __import__(modulename, globals(), locals(), [], -1)
    return getattr(moduleobject, classname)

def main():
    moduleobject = __import__(options.modulename, globals(), locals(), [], -1)
    classobject = getattr(moduleobject, options.objectname)
    editfile(classobject, options.modulename)
        
if __name__=='__main__':
    main()
    
        
        

    
