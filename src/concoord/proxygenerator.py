'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Proxy Generator that creates ConCoord proxy files from regular Python objects.
@copyright: See LICENSE
'''
import codegen
import ast, _ast
import os, shutil
import inspect, types, string

class ProxyGen(ast.NodeTransformer):
    def __init__(self, objectname, securitytoken=None):
        self.objectname = objectname
        self.inourobject = False
        self.token = securitytoken

    def generic_visit(self, node):
        ast.NodeTransformer.generic_visit(self, node)
        return node

    def visit_Module(self, node):
        importstmt = compile("from concoord.clientproxy import ClientProxy","<string>","exec",_ast.PyCF_ONLY_AST).body[0]
        node.body.insert(0, importstmt)
        return self.generic_visit(node)

    def visit_Import(self, node):
        return self.generic_visit(node)

    def visit_ImportFrom(self, node):
        return self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.inourobject = (node.name == self.objectname)
        if self.inourobject:
            for item in node.body:
                if type(item) == _ast.FunctionDef and item.name == "__init__":
                    item.name = "__concoordinit__"
            # Add the new init method
            initfunc = compile("def __init__(self, bootstrap):\n\tself.proxy = ClientProxy(bootstrap, token=%s)" % self.token,"<string>","exec",_ast.PyCF_ONLY_AST).body[0]
            node.body.insert(0, initfunc)
        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if self.inourobject:
            if node.name == "__init__":
                pass
            elif node.name == "__concoordinit__":
                args = ["\'__init__\'"]+[i.id for i in node.args.args[1:]]
                node.body = compile("return self.proxy.invoke_command(%s)" % ", ".join(args),"<string>","exec",_ast.PyCF_ONLY_AST).body
            else:
                args = ["\'"+ node.name +"\'"]+[i.id for i in node.args.args[1:]]
                node.body = compile("return self.proxy.invoke_command(%s)" % ", ".join(args),"<string>","exec",_ast.PyCF_ONLY_AST).body
            return node
        else:
            return self.generic_visit(node)

def createclientproxy(clientcode, objectname, securitytoken, bootstrap=None):
    # Get the AST tree, transform it, convert back to string
    originalast = compile(clientcode, "<string>", "exec", _ast.PyCF_ONLY_AST)
    newast = ProxyGen(objectname, securitytoken).visit(originalast)
    return codegen.to_source(newast)

