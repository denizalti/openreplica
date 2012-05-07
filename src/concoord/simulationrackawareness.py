'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Rack Awareness Simulator
@copyright: See LICENSE
'''
import re
import random
import sys, os

pdus = set()
tors = set()
heats = set()
machines = set()

class Tracker():
    def __init__(self, numreplicas, debug=True):
        """Tracker chooses a set of nodes to be started by the openreplicainitializer"""
        self.debug = debug
        self.numreplicas = numreplicas
        self.nodes = {}

        self.heatingfailures = 0
        self.pdufailures = 0
        self.machinefailures = 0
        self.torfailures = 0

    def parse_input_file(self, filename):
        inputfile = open(filename, 'r')
        for line in inputfile:
            line = re.sub(r'\s', '', line)
            name, desc = line.split(":")
            # rack,switch,cooling,machine
            self.nodes[name] = desc.split(',')
            pdu,tor,heat,machine = self.nodes[name]
            pdus.add(pdu)
            tors.add(tor)
            heats.add(heat)
            machines.add(machine)

    def pick_set_rackaware(self, totalcount):
        # pick the first node randomly
        randomname = random.choice(self.nodes.keys())
        randomdesc = self.nodes[randomname]
        picked = [randomname]
        alldesc = set(self.nodes[randomname])
        # pick rest of the nodes greedily
        while len(picked) < totalcount:
            maxtuple = (0,'')
            for i in range(1000):
                for name,desc in self.nodes.iteritems():
                    if name in picked and len(self.nodes) >= totalcount:
                        # a node should not be picked more than once
                        continue
                    differences = alldesc.difference(self.nodes[name])
                    if maxtuple[0] == 0 or len(differences) > maxtuple[0]:
                        print name, maxtuple[0]
                        maxtuple = (len(differences), name)
                picked.append(maxtuple[1])
            alldesc = alldesc.union(self.nodes[maxtuple[1]])
        return picked

    def pick_set_rackweighted(self, totalcount):
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

    def pick_set_random(self, totalcount):
        # pick all nodes randomly
        picked = []
        while len(picked) <= totalcount:
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

        # Probability of failures in 1000
        pdu = random.randint(1,3)
        tor =  random.randint(1,60)
        heat = random.randint(1,6)
        machine = random.randint(1,50)
        # Simulate it for a year
        for i in range(365):
            rackawaredict[i] = 0
            rackweighteddict[i] = 0
            randomdict[i] = 0
            failures = []

            # first decide on failures
            if pdu > 0:
                p = random.choice(list(pdus))
                failures.append(p)
                pdu -= 1

            if tor > 0:
                p = random.choice(list(tors))
                failures.append(p)
                tor -= 1

            if heat > 0:
                p = random.choice(list(heats))
                failures.append(p)
                heat -= 1

            if machine > 0:
                p = random.choice(list(machines))
                failures.append(p)
                machine -= 1

            allfailures = 0
            for f in failures:
                for node in rackawarelist:
                    if f in self.nodes[node]:
                        allfailures += 1
                if allfailures > self.numreplicas/2:
                    #print f, self.nodes[node], node
                    rackawaredict[i] += 1

            allfailures = 0
            for f in failures:
                for node in rackweightedlist:
                    if f in self.nodes[node]:
                        allfailures += 1
                if allfailures > self.numreplicas/2:
                    #print">> ", f, self.nodes[node], node
                    rackweighteddict[i] += 1

            allfailures = 0
            for f in failures:
                for node in randomlist:
                    if f in self.nodes[node]:
                        allfailures += 1
                if allfailures > self.numreplicas/2:
                    #print ">>>>", f, self.nodes[node], node
                    randomdict[i] += 1

        return rackawaredict, rackweighteddict, randomdict


    def results(self, rackawaredict, rackweighteddict, randomdict):
        racktotal = 0
        rackweightedtotal = 0
        randomtotal = 0
        for i,j in rackawaredict.iteritems():
            racktotal += 1

        for i,j in rackweighteddict.iteritems():
            rackweightedtotal += j

        for i,j in randomdict.iteritems():
            randomtotal += j

        return racktotal, rackweightedtotal, randomtotal
    
def main():
    filename = 'trackerfile'
    numreplicas = int(sys.argv[1])
    t = Tracker(numreplicas)
    t.parse_input_file(filename)
    racktotal = 0
    rackweightedtotal = 0
    randomtotal = 0

    picked_nodes_rackaware = t.pick_set_rackaware(numreplicas)
    os._exit(0)

    for i in range(1):
        # pick nodes in a rack-aware manner
        picked_nodes_rackaware = t.pick_set_rackaware(numreplicas)
        # pick nodes in a rack-aware manner
        picked_nodes_rackweighted = t.pick_set_rackweighted(numreplicas)
        # pick nodes randomly
        picked_nodes_random = t.pick_set_random(numreplicas)
        print "Rack Aware: ", picked_nodes_rackaware
        #print "Rack Weighted: ", picked_nodes_rackweighted
        #print "Random: ", picked_nodes_random
        
        for i in range(1):
            rackawaredict, rackweighteddict, randomdict = t.simulatefailures(picked_nodes_rackaware, picked_nodes_rackweighted, picked_nodes_random)
            print rackawaredict
            results = t.results(rackawaredict, rackweighteddict, randomdict)
            racktotal += results[0]
            rackweightedtotal += results[1]
            randomtotal += results[2]
        
    print racktotal, randomtotal

    #print t.heatingfailures, t.pdufailures, t.machinefailures, t.torfailures
    
if __name__=='__main__':
    main()
