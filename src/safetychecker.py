import compiler
import ast, _ast
import os
from modulefinder import ModuleFinder
from optparse import OptionParser

parser = OptionParser(usage="usage: %prog -s subdomain -n objectname -o objectcode -r replicas")
parser.add_option("-n", "--objectname", action="store", dest="objectname", help="client object name")
parser.add_option("-o", "--objectcode", action="store", dest="objectcode", help="client object code")
(options, args) = parser.parse_args()

DEBUG = True

class Visitor(ast.NodeVisitor):
    def generic_visit(self, node):
        print "---", ast.dump(node)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_Import(self, node):
        print "No imports allowed.. --> EXIT"
        
    def visit_Call(self, node):
        if DEBUG:
            print 'Call : '
        self.check_functioncall(node)
        self.generic_visit(node)

    def visit_Name(self, node):
        if DEBUG:
            print 'Name :', node.id

    def visit_Num(self, node):
        if DEBUG:
            print 'Num :', node.__dict__['n']

    def visit_Str(self, node):
        if DEBUG:
            print "Str :", node.s

    def visit_Print(self, node):
        if DEBUG:
            print "Print :"
        self.generic_visit(node)

    def visit_Assign(self, node):
        if DEBUG:
            print "Assign :"
        self.generic_visit(node)

    def visit_Expr(self, node):
        if DEBUG:
            print "Expr :"
        self.generic_visit(node)

    def addassignment(self, node):
        global assignments
        print "Adding assignment.."
        for target in node.targets:
            if type(target).__name__ == 'Name':
               if type(node.value).__name__ == 'Name':
                   assignments[target.id] = assignments[node.value.id]
            elif type(target).__name__ == 'Attribute':
                pass
                
        for fname,fvalue in ast.iter_fields(node):
            if DEBUG:
                print fname, " ", fvalue

    def check_functioncall(self, node):
        if DEBUG:
            print "Checking function call.."
        isopen=issetattr=isgetattr=iscompile=isexec=iseval= False
        for fname,fvalue in ast.iter_fields(node):
            if DEBUG:
                print fname, " ", fvalue
            #XXX: Do this in a more pythonic way
            if type(fvalue).__name__ == 'Name':
                #XXX: The Name doesn't have to be the original
                #XXX: could be overwritten
                if fvalue.id == 'open':
                    isopen = True
                elif fvalue.id == 'setattr':
                    issetattr = True
                    print "Can't setattr --> EXIT"
                elif fvalue.id == 'getattr':
                    isgetattr = True
                    print "Can't getattr --> EXIT"
                elif fvalue.id == 'compile':
                    iscompile = True
                    print "Can't compile --> EXIT"
                elif fvalue.id == 'execfile':
                    isexec = True
                    print "Can't execute --> EXIT"
                elif fvalue.id == 'eval':
                    iseval = True
                    print "Can't evaluate --> EXIT"
            if fname == 'args' and type(fvalue).__name__ == 'Str':
                for arg in fvalue:
                    if arg.__dict__['s'] == 'w' or arg.__dict__['s'] == 'a' and isopen:
                        print "Writing to file.. --> EXIT"
            if fname == 'args' and type(fvalue).__name__ == 'Name':
                for arg in fvalue:
                    if arg.__dict__['n'] == 'w' or arg.__dict__['s'] == 'a' and isopen:
                        print "Writing to file.. --> EXIT"
        os._exit(0)
def main():
    path = "/Users/denizalti/paxi/src/obj/bank.py"
    astnode = compile(open(path, 'rU').read(),"<string>","exec",_ast.PyCF_ONLY_AST)

    v = Visitor()
    v.visit(astnode)

    #print astnode.body[0].names[0].name
    #for child in ast.iter_child_nodes(astnode):
    #    print ast.dump(child)

    #astnode = compiler.parse(open(path, 'rU').read())
    #print astnode.getChildren()
    #print str(astnode)

def check_imports(path):
    finder = ModuleFinder()
    finder.run_script(path)
    modules = []
    print 'Loaded modules:'
    for name, mod in finder.modules.iteritems():
        print '%s ' % name
        if name != "__main__":
            return False
    return True

if __name__=='__main__':
    main()

