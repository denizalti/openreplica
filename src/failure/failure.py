from datacenter import *


def in_all(allsets):
    intersectall = allsets[0]
    for s in allsets:
        intersectall = intersectall.intersection(s)
    return intersectall

def only_in(set1, allsets):
    unionall = set()
    for s in allsets:
        if s != set1:
            unionall = unionall.union(s)
    return set1.difference(unionall)

dc = Datacenter(10)

A = set([dc.P1,dc.P2,dc.P4,dc.P5])
B = set([dc.P1,dc.P2,dc.P3,dc.P6])
C = set([dc.P1,dc.P3,dc.P4,dc.P7])
allsets = [A,B,C]

# First find the events that kill them all
finalprobabilitiestoadd = in_all(allsets)

# Now find events that kill only one of them
for s in allsets:
    onlyins = only_in(s, allsets)


