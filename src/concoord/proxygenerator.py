'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Proxy Generator that creates ConCoord proxy files from regular Python objects.
@date: March 20, 2011
@copyright: See COPYING.txt
'''
import inspect, types, string
import os, shutil
import ast, _ast
import codegen

class ProxyGen(ast.NodeTransformer):
    def __init__(self, objectname):
        self.objectname = objectname
        self.inourobject = False

    def generic_visit(self, node):
        ast.NodeTransformer.generic_visit(self, node)
        return node

    def visit_Module(self, node):
        importstmt = compile("import clientproxy","<string>","exec",_ast.PyCF_ONLY_AST).body
        node.body.insert(0, importstmt[0])
        return self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.inourobject = (node.name == self.objectname)
        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if self.inourobject:
            # XXX this code currently only supports positional arguments
            if node.name == "__init__":
                node.args.args.append(ast.Name(id="bootstrap"))
                args = [i.id for i in node.args.args[1:]]
                node.body = compile("self.proxy = clientproxy.ClientProxy(" + ", ".join(args) +")","<string>","exec",_ast.PyCF_ONLY_AST).body
            else:
                args = [i.id for i in node.args.args[1:]]
                node.body = compile("return self.proxy.invoke_command(\"" + node.name +"\", "+", ".join(args)+")","<string>","exec",_ast.PyCF_ONLY_AST).body
            return node
        else:
            return self.generic_visit(node)

def createclientproxy(clientcode, objectname, bootstrap=None):
    # Get the AST tree, transform it, convert back to string
    originalast = compile(clientcode, "<string>", "exec", _ast.PyCF_ONLY_AST)
    newast = ProxyGen(objectname).visit(originalast)
    return codegen.to_source(newast)

