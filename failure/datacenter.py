from random import *
from optparse import OptionParser

parser = OptionParser(usage="usage: %prog -p port -b bootstrap -d delay")
parser.add_option("-p", "--prob", action="store", dest="numprobabilities", type="int", help="number of probabilities for the datacenter")

(options, args) = parser.parse_args()

RANDOMIZATION = 10000.0

class Datacenter():
    def __init__(self, numprobabilities):
        for i in range(numprobabilities):
            setattr(self, "P"+str(i), randrange(0, RANDOMIZATION)/RANDOMIZATION)

    def __str__(self):
        return str(dir(self))

def main():
    theDatacenter = Datacenter(options.numprobabilities)
    print str(theDatacenter)

if __name__=='__main__':
    main()
