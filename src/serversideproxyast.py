import inspect, types, string
import os, shutil
import ast, _ast
#from optparse import OptionParser

#parser = OptionParser(usage="usage: %prog -m modulename -o objectname")
#parser.add_option("-m", "--modulename", action="store", dest="modulename", help="name for the module (filename)")
#parser.add_option("-o", "--objectname", action="store", dest="objectname", help="name for the object (class definition name)")
#(options, args) = parser.parse_args()

class ServerVisitor(ast.NodeVisitor):
    def __init__(self, objectname):
        self.objectname = objectname
        self.functionstofix = {}
    
    def generic_visit(self, node):
        ast.NodeVisitor.generic_visit(self, node)

    def visit_ClassDef(self, node):
        if node.name == self.objectname:
            self.getfunctionsofclass(node)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        self.editfunctiondef(node)
        self.generic_visit(node)

    def getfunctionsofclass(self, node):
        for functiondef in node.body:
            self.functionstofix[functiondef.lineno] = functiondef
            
    def editfunctiondef(self, node):
        for fname,fnode in ast.iter_fields(node):
            if fname == 'args':
                for argname, argnode in ast.iter_fields(fnode):
                    if argname == 'kwarg' and argnode != None:
                        del self.functionstofix[node.lineno]

        if node.lineno in self.functionstofix.keys():
            print "%d | Fixing function definition." % (node.lineno)

def editproxyfile(modulename, objectname):
    abspath = os.path.abspath(modulename+'.py')
    # Get the AST tree, find lines to fix
    astnode = compile(open(abspath, 'rU').read(),"<string>","exec",_ast.PyCF_ONLY_AST)
    v = ServerVisitor(objectname)
    v.visit(astnode)
    functionstofix = v.functionstofix
    # Get the contents of the file
    abspath = os.path.abspath(modulename+'.py')
    objectfile = open(abspath, 'r')
    filecontent = {}
    i = 1
    for line in objectfile:
        filecontent[i] = line
        i += 1
    objectfile.close()
    # Edit the file
    for line, function in functionstofix.iteritems():
        filecontent[line] = string.replace(filecontent[line], "):", ", **kwargs):", 1)
    objectfile = open(abspath+"fixed", 'w')
    for line, content in filecontent.iteritems():
        objectfile.write(content)
    objectfile.close()
    return objectfile
    
#def main():
#    editproxyfile(options.modulename, options.objectname)
        
#if __name__=='__main__':
#    main()
    
        
        

    
