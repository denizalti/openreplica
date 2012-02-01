import os, time
import md5
from openreplicacoordobjproxy import OpenReplicaCoordProxy

def getlatestfile(filenames):
    latest = filenames[0]
    for filename in filenames:
        if filename > latest:
            latest = filename
    return latest

def main():
    openreplicacoordobj = OpenReplicaCoordProxy('openreplica.org')
    newobjectstate = openreplicacoordobj.__str__()
    filenames = []
    for filename in os.listdir('/tmp/'):
        if filename.endswith('-ORobject'):
            filenames.append(filename)
    oldobjectstate = open('/tmp/'+getlatestfile(filenames),'r').read()
    m = md5.new()
    m.update(newobjectstate)
    newmd5 = m.digest()
    m = md5.new()
    m.update(oldobjectstate)
    oldmd5 = m.digest()

    if oldmd5 != newmd5:
        f = open('/tmp/'+time.strftime("%Y.%m.%d.%H.%M.%S", time.gmtime())+'-ORobject','w')
        f.write(newobjectstate)
        f.close()
    
if __name__=='__main__':
    main()
