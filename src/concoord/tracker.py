'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: ConCoord Node Tracker
@copyright: See LICENSE
'''
import re
import random
from concoord.enums import *
from concoord.utils import *
from concoord.openreplica.plmanager import *
from concoord.openreplica.openreplicaaddnode import *
from concoord.openreplica.openreplicainitializer import *

class Tracker():
    def __init__(self, debug=True):
        """Tracker chooses a set of nodes to be started by the openreplicainitializer"""
        self.debug = debug
        self.nodes = {}

    def parse_input_file(self, filename):
        inputfile = open(filename, 'r')
        for line in inputfile:
            line = re.sub(r'\s', '', line)
            name, desc = line.split(":")
            # wing,power_supply,ac_feed,switch,rack,position
            self.nodes[name] = desc.split(',')

    def pick_set(self, config):
        numreplicas, numacceptors, numnameservers = config
        totalcount = numreplicas + numacceptors + numnameservers
        # pick the first node randomly
        randomname = random.choice(self.nodes.keys())
        randomdesc = self.nodes[randomname]
        picked = [randomname]
        alldesc = set(self.nodes[randomname])
        # pick rest of the nodes greedily
        while len(picked) < totalcount-1:
            maxtuple = (0,'')
            for name,desc in self.nodes.iteritems():
                if name in picked and len(self.nodes) >= totalcount:
                    # a node should not be picked more than once
                    continue
                differences = alldesc.difference(self.nodes[name])
                if maxtuple[0] == 0 or len(differences) > maxtuple[0]:
                    maxtuple = (len(differences), name)
            picked.append(maxtuple[1])
            alldesc = alldesc.union(self.nodes[maxtuple[1]])
        return picked
    
def main():
    filename = 'trackerfile'
    config = (2,1,1)
    t = Tracker()
    t.parse_input_file(filename)
    picked_nodes = t.pick_set(config)
    # initialize the system with picked nodes
    node_connections = []
    for node in picked_nodes:
        node_connections.append(PLConnection(nodes=[node], configdict=CONFIGDICT))
    
if __name__=='__main__':
    main()



    
