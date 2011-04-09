from optparse import OptionParser

from node import Node, options
from enums import NODE_NAMESERVER

def main():
    nameservernode = Node(NODE_NAMESERVER, bootstrap=options.bootstrap)
    nameservernode.startnameserver()

if __name__=='__main__':
    main()
