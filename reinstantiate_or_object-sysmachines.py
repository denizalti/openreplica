from concoord.proxy.nameservercoord import *

n = NameserverCoord("openreplica.org")
objstate = open('ORstate', 'r').read().strip()
print objstate
n._reinstantiate(objstate)
