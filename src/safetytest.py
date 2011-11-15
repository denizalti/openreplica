import sys
from time import time

class SafetyTest():
    def __init__(self):
        self.accounts = {}

    def importtest(self, args):
        a = 7
        b = 8
        import os
        c = a + b

    def filetest(self, args):
        f = open('/testfile', 'w')
        f = open('/testfile', 'a')
	test = 'w'
        f = open('/testfile', test)

    def directcalltest(self, args):
        code = compile('a = 1 + 2', '<string>', 'exec')
        exec code
        print a
        
    def indirectcalltest(self, args):
        g = getattr
        test = Test()
        g(test, 'bar')

class Test():
    def __init__(self):
        self.bar = 789
