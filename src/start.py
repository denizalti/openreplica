import os
import sys

for i in range(int(sys.argv[1])):
    if os.fork() == 0:
        print "in the child"
        sys.stdin.close()
        os.execv('/bin/sleep', ['/bin/sleep','10'])
