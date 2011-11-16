import xmlrpclib
import sys

s = xmlrpclib.ServerProxy('https://www.planet-lab.org/PLCAPI/', allow_none=True)
# Specify password authentication
auth = {'Username': 'denizalti@gmail.com',
        'AuthString': '11235813',
        'AuthMethod': 'password'}
authorized = s.AuthCheck(auth)
if not authorized:
    print 'Authorization failed!'

def listallnodes():
    print 'Getting all nodes!'
    all_nodes = s.GetNodes(auth)
    for node in all_nodes:
        print node['hostname']

def writeallnodestofile():
    f = open("plnodes.txt", 'w')
    all_nodes = s.GetNodes(auth)
    for node in all_nodes:
        f.write(node['hostname']+"\n")
    f.close()

def addnodes(nodes):
    slice_id = s.GetSlices(auth, ['cornell_openreplica'], ['slice_id'])[0]['slice_id']
    s.AddSliceToNodes(auth, slice_id, nodes)

def shownodes():
    node_ids = s.GetSlices(auth, ['cornell_openreplica'], ['node_ids'])[0]['node_ids']
    node_hostnames = [node['hostname'] for node in s.GetNodes(auth, node_ids, ['hostname'])]
    print node_hostnames

def getallnodes():
    all_nodes = s.GetNodes(auth)
    nodenames = []
    for node in all_nodes:
        nodenames.append(node['hostname'])
    return nodenames

def main():
    pass
    
if __name__ == '__main__':
    sys.exit(main())


