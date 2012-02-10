'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Script to save openreplica coordination object automatically
@date: August 1, 2011
@copyright: See LICENSE
'''
from openreplicacoordobjproxy import OpenReplicaCoordProxy

def main():
    openreplicacoordobj = OpenReplicaCoordProxy('openreplica.org')
    print openreplicacoordobj.__str__()
    
if __name__=='__main__':
    main()
