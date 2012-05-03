'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Rack Awareness Simulator
@copyright: See LICENSE
'''
import re
import random

pdus = ['main', 'main0']
tors =  ['ac1', 'ac2', 'ac10', 'ac20']
heats = ['p1','p2', 'p10','p20']
machines = ['u1','u2','u3','u4','u5','u6','u7','u8','u9','u10','u11','u12','u13','u20','u30','u40','u50','u60','u70','u80','u90','u100','u110','u120']  

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
            # rack,switch,cooling,machine
            self.nodes[name] = desc.split(',')

    def pick_set_rackaware(self, config):
        numreplicas, numacceptors, numnameservers = config
        totalcount = numreplicas + numacceptors + numnameservers
        # pick the first node randomly
        randomname = random.choice(self.nodes.keys())
        randomdesc = self.nodes[randomname]
        picked = [randomname]
        alldesc = set(self.nodes[randomname])
        # pick rest of the nodes greedily
        while len(picked) < totalcount:
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

    def pick_set_rackweighted(self, config):
        numreplicas, numacceptors, numnameservers = config
        totalcount = numreplicas + numacceptors + numnameservers
        # pick the first node randomly
        randomname = random.choice(self.nodes.keys())
        picked = [randomname]
        alldesc = set(self.nodes[randomname])
        # pick rest of the nodes greedily
        while len(picked) < totalcount:
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

    def pick_set_random(self, config):
        numreplicas, numacceptors, numnameservers = config
        totalcount = numreplicas + numacceptors + numnameservers
        # pick the first node randomly
        picked = []
        # pick rest of the nodes greedily
        while len(picked) < totalcount:
            picked.append(random.choice(self.nodes.keys()))
        return picked

    def simulatefailures(self, rackawarelist, rackweightedlist, randomlist):
        #pdu: 1 in a year
        #toR failure: 0.05 \cite{Gill:2011}
        #overheating: 0.5 in a year
        #machine failure: 1000 in a year \cite{Dean}

        rackawaredict = {}
        rackweighteddict = {}
        randomdict = {}
        
        pdu = 3
        tor =  60
        heat = 6
        machine = 50
        for i in range(365):
            rackawaredict[i] = 0
            rackweighteddict[i] = 0
            randomdict[i] = 0
            failures = []
            # first decide on failures
            for p in pdus:
                randomnum = random.randint(1,1000)
                if randomnum <= pdu:
                    failures.append(p)
            for t in tors:
                randomnum = random.randint(1,1000)
                if randomnum <= tor:
                    failures.append(t)
            for h in heats:
                randomnum = random.randint(1,1000)
                if randomnum <= heat:
                    failures.append(h)
            for m in machines:
                randomnum = random.randint(1,1000)
                if randomnum <= machine:
                    failures.append(m)

            allfailures = 0
            for f in failures:
                for node in rackawarelist:
                    if f in self.nodes[node]:
                        allfailures += 1
                if allfailures > 2:
                    #print f, self.nodes[node], node
                    rackawaredict[i] += 1

            allfailures = 0
            for f in failures:
                for node in rackweightedlist:
                    if f in self.nodes[node]:
                        allfailures += 1
                if allfailures > 2:
                    #print">> ", f, self.nodes[node], node
                    rackweighteddict[i] += 1

            allfailures = 0
            for f in failures:
                for node in randomlist:
                    if f in self.nodes[node]:
                        allfailures += 1
                if allfailures > 2:
                    #print ">>>>", f, self.nodes[node], node
                    randomdict[i] += 1

        return rackawaredict, rackweighteddict, randomdict

    def results(self, rackawaredict, rackweighteddict, randomdict):
        racktotal = 0
        rackweightedtotal = 0
        randomtotal = 0
        for i,j in rackawaredict.iteritems():
            racktotal += j

        for i,j in rackweighteddict.iteritems():
            rackweightedtotal += j

        for i,j in randomdict.iteritems():
            randomtotal += j

        return racktotal, rackweightedtotal, randomtotal
    
def main():
    filename = 'trackerfile'
    config = (1,1,0)
    t = Tracker()
    t.parse_input_file(filename)
    for i in range(10):
        # pick nodes in a rack-aware manner
        picked_nodes_rackaware = t.pick_set_rackaware(config)
        # pick nodes in a rack-aware manner
        picked_nodes_rackweighted = t.pick_set_rackweighted(config)
        # pick nodes randomly
        picked_nodes_random = t.pick_set_random(config)
        #print "Rack Aware: ", picked_nodes_rackaware
        #print "Rack Weighted: ", picked_nodes_rackweighted
        #print "Random: ", picked_nodes_random
        
        racktotal = 0
        rackweightedtotal = 0
        randomtotal = 0
        for i in range(10):
            rackawaredict, rackweighteddict, randomdict = t.simulatefailures(picked_nodes_rackaware, picked_nodes_rackweighted, picked_nodes_random)
            results = t.results(rackawaredict, rackweighteddict, randomdict)
            racktotal += results[0]
            rackweightedtotal += results[1]
            randomtotal += results[2]
        
    print racktotal/100.0, rackweightedtotal/100.0, randomtotal/100.0
    
if __name__=='__main__':
    main()
