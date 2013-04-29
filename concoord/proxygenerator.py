'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Proxy Generator that creates ConCoord proxy files from regular Python objects.
@copyright: See LICENSE
'''
import codegen
import ast, _ast
import os, shutil
import inspect, types, string
from concoord.enums import PR_BASIC, PR_BLOCK, PR_CBATCH, PR_SBATCH

class ProxyGen(ast.NodeTransformer):
    def __init__(self, objectname, securitytoken=None, proxytype=0):
        self.objectname = objectname
        self.classdepth = 0
        self.token = securitytoken
        self.proxytype = proxytype

    def generic_visit(self, node):
        ast.NodeTransformer.generic_visit(self, node)
        return node

    def visit_Module(self, node):
        if self.proxytype == PR_BASIC:
            importstmt = compile("from concoord.clientproxy import ClientProxy","<string>","exec",_ast.PyCF_ONLY_AST).body[0]
        elif self.proxytype == PR_BLOCK:
            importstmt = compile("from concoord.blockingclientproxy import ClientProxy","<string>","exec",_ast.PyCF_ONLY_AST).body[0]
        elif self.proxytype == PR_CBATCH:
            importstmt = compile("from concoord.batchclientproxy import ClientProxy","<string>","exec",_ast.PyCF_ONLY_AST).body[0]
        elif self.proxytype == PR_SBATCH:
            importstmt = compile("from concoord.asyncclientproxy import ClientProxy","<string>","exec",_ast.PyCF_ONLY_AST).body[0]
        node.body.insert(0, importstmt)
        return self.generic_visit(node)

    def visit_Import(self, node):
        return self.generic_visit(node)

    def visit_ImportFrom(self, node):
        return self.generic_visit(node)

    def visit_ClassDef(self, node):
        selectedclass = node.name == self.objectname
        if selectedclass or self.classdepth:
            self.classdepth += 1
        if self.classdepth == 1:
            for item in node.body:
                if type(item) == _ast.FunctionDef and item.name == "__init__":
                    #node.body.remove(item)
                    item.name = "__concoordinit__"
            # Add the new init method
            initfunc = compile("def __init__(self, bootstrap):\n"
                               "\tself.proxy = ClientProxy(bootstrap, token=\"%s\")" % self.token,
                               "<string>",
                               "exec",
                               _ast.PyCF_ONLY_AST).body[0]
            node.body.insert(0, initfunc)
        ret = self.generic_visit(node)
        if selectedclass or self.classdepth:
            self.classdepth -= 1
        return ret

    def visit_FunctionDef(self, node):
        if self.classdepth == 1:
            for i in node.args.args:
                if i.id == '_concoord_command':
                    node.args.args.remove(i)
            if node.name == "__init__":
                pass
            else:
                args = ["\'"+ node.name +"\'"]+[i.id for i in node.args.args[1:]]
                node.body = compile("return self.proxy.invoke_command(%s)" % ", ".join(args),
                                    "<string>",
                                    "exec",
                                    _ast.PyCF_ONLY_AST).body
            return node
        else:
            return self.generic_visit(node)

def createclientproxy(clientcode, objectname, securitytoken, proxytype=PR_BASIC, bootstrap=None):
    # Get the AST tree, transform it, convert back to string
    originalast = compile(clientcode, "<string>", "exec", _ast.PyCF_ONLY_AST)
    newast = ProxyGen(objectname, securitytoken, proxytype).visit(originalast)
    return codegen.to_source(newast)

