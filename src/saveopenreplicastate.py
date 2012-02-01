from openreplicacoordobjproxy import OpenReplicaCoordProxy

def main():
    openreplicacoordobj = OpenReplicaCoordProxy('openreplica.org')
    print openreplicacoordobj.__str__()
    
if __name__=='__main__':
    main()
