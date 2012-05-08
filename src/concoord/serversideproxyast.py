'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Fixes client objects to be replicated by ConCoord
@copyright: See LICENSE
'''
import inspect, types, string
import os, shutil, sys
import ast, _ast

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
            if functiondef.name == "__init__":
                self.initline = functiondef.lineno
            self.functionstofix[functiondef.lineno] = functiondef
            
    def editfunctiondef(self, node):
        for fname,fnode in ast.iter_fields(node):
            if fname == 'args':
                for argname, argnode in ast.iter_fields(fnode):
                    if argname == 'kwarg' and argnode != None:
                        del self.functionstofix[node.lineno]

        if node.lineno in self.functionstofix.keys():
            print "%d | Fixing function definition." % (node.lineno)

def editproxyfile(filepath, objectname, securitytoken):
    # Get the AST tree, find lines to fix
    astnode = compile(open(filepath, 'rU').read(),"<string>","exec",_ast.PyCF_ONLY_AST)
    v = ServerVisitor(objectname)
    v.visit(astnode)
    functionstofix = v.functionstofix
    # Get the contents of the file
    objectfile = open(filepath, 'r')
    filecontent = {}
    i = 1
    for line in objectfile:
        filecontent[i] = line
        i += 1
    objectfile.close()
    # Edit the file
    for line, function in functionstofix.iteritems():
        filecontent[line] = string.replace(filecontent[line], "):", ", **kwargs):", 1)
    objectfile = open(filepath+"fixed", 'w')
    for line, content in filecontent.iteritems():
        if line == v.initline:
            objectfile.write(content)
            objectfile.write("\tself.__concoord_token = \"%s\"\n" % securitytoken)
        else:    
            objectfile.write(content)
    objectfile.close()
    return objectfile

def main():
    editproxyfile(sys.argv[1], sys.argv[2], sys.argv[3])
    
if __name__=='__main__':
    main()
