import ast, _ast
DEBUG = False

class Visitor(ast.NodeVisitor):
    def generic_visit(self, node):
        if DEBUG:
            print "---", ast.dump(node)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_Import(self, node):
        print "%d | No imports allowed: %s --> EXIT" % (node.lineno,node.names[0].name)

    def visit_ImportFrom(self, node):
        print "%d | No imports allowed: %s --> EXIT" % (node.lineno,node.module)

    def visit_Exec(self, node):
        print "%d | Exec not allowed --> EXIT" % node.lineno
        
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
                print "%d | Function assignment: %s --> EXIT" % (node.lineno,node.value.id)

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
                    print "%d | Forbidden function call: %s --> EXIT" % (node.lineno,fvalue.id)
            if fname == 'args':
                for arg in fvalue:
                    if type(arg).__name__ == 'Str':
                        if arg.__dict__['s'] == 'w' or arg.__dict__['s'] == 'a' and isopen:
                            print "%d | Write to file --> EXIT" % node.lineno
                    elif type(arg).__name__ == 'Name':
                        print "%d | File operation with variable argument: %s --> EXIT" % (node.lineno,arg.id)
def main():
    path = "/Users/denizalti/paxi/src/safetytest.py"
    astnode = compile(open(path, 'rU').read(),"<string>","exec",_ast.PyCF_ONLY_AST)
    v = Visitor()
    v.visit(astnode)

if __name__=='__main__':
    main()

