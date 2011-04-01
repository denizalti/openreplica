from optparse import OptionParser

from node import Node
from enums import NODE_NAMESERVER

parser = OptionParser(usage="usage: %prog -p port -b bootstrap -d delay")
parser.add_option("-p", "--port", action="store", dest="port", type="int", default=6668, help="port for the node")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port:type triple for the bootstrap peer")

(options, args) = parser.parse_args()

def main():
    nameservernode = Node(NODE_NAMESERVER, bootstrap=options.bootstrap)
    nameservernode.startnameserver()

if __name__=='__main__':
    main()
