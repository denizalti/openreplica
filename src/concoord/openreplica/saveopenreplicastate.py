'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Script to save openreplica coordination object automatically
@copyright: See LICENSE
'''
from concoord.openreplica.openreplicacoordobjproxy import OpenReplicaCoordProxy

def main():
    openreplicacoordobj = OpenReplicaCoordProxy('openreplica.org')
    print openreplicacoordobj.__str__()
    
if __name__=='__main__':
    main()
