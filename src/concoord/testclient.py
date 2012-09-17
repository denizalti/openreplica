from concoord.proxy.test import *
from optparse import OptionParser

parser = OptionParser(usage="usage: %prog -a addr -p port -b bootstrap -f objectfilename -c objectname -n subdomainname -d debug")
parser.add_option("-b", "--boot", action="store", dest="bootstrap", help="address:port:type triple for the bootstrap peer")
(options, args) = parser.parse_args()

t = Test(options.bootstrap)
for i in range(10300):
  t.getvalue()
