from obj import *
import inspect

def get_functions(classobj):
    functionslist = dir(classobj)
    for function in functionslist:
        if function.startswith("__"):
            del(function)
    return functionslist

def get_arguments(function):
    args, _, _, values = inspect.getargspec(function)
    return args
