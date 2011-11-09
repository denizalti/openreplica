import compiler
import ast, _ast
import os
from modulefinder import ModuleFinder
from optparse import OptionParser

parser = OptionParser(usage="usage: %prog -s subdomain -n objectname -o objectcode -r replicas")
parser.add_option("-n", "--objectname", action="store", dest="objectname", help="client object name")
parser.add_option("-o", "--objectcode", action="store", dest="objectcode", help="client object code")
(options, args) = parser.parse_args()

DEBUG = False

class Visitor(ast.NodeVisitor):
    def generic_visit(self, node):
        if DEBUG:
            print "---", ast.dump(node)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_Import(self, node):
        print "No imports allowed: %s --> EXIT" % node.names[0].name

    def visit_ImportFrom(self, node):
        print "No imports allowed: %s --> EXIT" % node.module

    def visit_Exec(self, node):
        print "Exec not allowed --> EXIT"
        
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
        self.check_assignment(node)
        self.generic_visit(node)

    def visit_Expr(self, node):
        if DEBUG:
            print "Expr :"
        self.generic_visit(node)

    def check_assignment(self, node):
        if DEBUG:
            print "Checking assignment.."
        inapplicable = ["open","setattr","getattr","compile","exec","eval","execfile"]
        if type(node.value).__name__ == 'Name':
            if node.value.id in inapplicable:
                print "Function assignment: %s --> EXIT" % node.value.id

    def check_functioncall(self, node):
        if DEBUG:
            print "Checking function call.."
        inapplicable = ["setattr","getattr","compile","exec","eval","execfile"]
        isopen = False
        for fname,fvalue in ast.iter_fields(node):
            if DEBUG:
                print fname, " ", fvalue
            if fname == 'func' and type(fvalue).__name__ == 'Name':
                if fvalue.id == 'open':
                    isopen = True
                elif fvalue.id in inapplicable:
                    print "Forbidden function call: %s --> EXIT" % fvalue.id
            if fname == 'args':
                for arg in fvalue:
                    if type(arg).__name__ == 'Str':
                        if arg.__dict__['s'] == 'w' or arg.__dict__['s'] == 'a' and isopen:
                            print "Write to file --> EXIT"
                    elif type(arg).__name__ == 'Name':
                        print "File operation with variable argument: %s --> EXIT" % arg.id
def main():
    path = "/Users/denizalti/paxi/src/safetytest.py"
    astnode = compile(open(path, 'rU').read(),"<string>","exec",_ast.PyCF_ONLY_AST)
    v = Visitor()
    v.visit(astnode)

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

