import inspect
from optparse import OptionParser


from obj import *

parser = OptionParser(usage="usage: %prog -o --obj objectname")
parser.add_option("-o", "--obj", action="store", dest="objectname", help="name of the object to be converted to a proxy")
(options, args) = parser.parse_args()

def get_functions_of_obj(classobj):
    functionslist = dir(classobj)
    for function in functionslist:
        if function.startswith("__"):
            del(function)
    return functionslist

def get_arguments_of_func(function):
    args, _, _, values = inspect.getargspec(function)
    return args

def dict_to_parameterized(class_name,parameter_values):
    parameter_objs = dict([(name,Parameter(default=value))
                           for name,value in parameter_values.items()])
    new_class = new.classobj(class_name,(Representer,),parameter_objs)
    return  new_class(parameter_values)


options.objectname
