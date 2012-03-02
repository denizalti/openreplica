'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Script to save openreplica coordination object automatically
@copyright: See LICENSE
'''
from concoord.proxy.openreplicacoord import OpenReplicaCoord

def main():
    openreplicacoord = OpenReplicaCoord('openreplica.org')
    print openreplicacoord.__str__()
    
if __name__=='__main__':
    main()
