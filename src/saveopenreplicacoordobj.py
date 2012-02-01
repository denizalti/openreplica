import time
import subprocess
from openreplicacoordobjproxy import OpenReplicaCoordProxy

openreplicacoordobj = OpenReplicaCoordProxy('openreplica.org')
objectstate = openreplicacoordobj.__str__()
print "************", objectstate
f = open('/tmp/'+time.strftime("%Y.%m.%d.%H.%M.%S", time.gmtime())+'-ORobject','w')
f.write(objectstate)
f.close()
#cmd = ['cat', '/tmp/'+time.strftime("%Y.%m.%d.%H.%M.%S", time.gmtime())+'-ORobject']
#p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#print p.communicate()
