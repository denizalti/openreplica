import socket
import time
import string
from enums import *

def findOwnIP():
    """Retrieves the hostname of the caller"""
    return socket.gethostbyname(socket.gethostname())

logprefix = None

def setlogprefix(logpre):
    global logprefix
    logprefix = logpre

def logger(logstr):
    if logprefix:
        print "[%s] %s" % (logprefix, logstr)

timers = {}
def starttimer(timerkey, timerno):
    global timers
    index = "%s-%s" % (str(timerkey),str(timerno))
    if not timers.has_key(index):
        timers[index] = [time.time(), 0]

def endtimer(timerkey, timerno):
    global timers
    index = "%s-%s" % (str(timerkey),str(timerno))
    try:
        if timers[index][1] == 0:
            timers[index][1] = time.time()
    except:
        print "Can't stop timer %s %s." % (str(timerkey),str(timerno))
    
def dumptimers(numreplicas, numacceptors, ownertype):
    global timers
    if ownertype == NODE_LEADER or ownertype == NODE_REPLICA:
        filename = "output/replica/%s-%s" % (str(numreplicas), str(numacceptors))
    elif ownertype == NODE_ACCEPTOR:
        filename = "output/acceptor/%s-%s" % (str(numreplicas), str(numacceptors))
    try:
        # XXX hardcoded output file
        outputfile = open("/home/deniz/concoord/"+filename, "w")
    except:
        outputfile = open("./"+filename, "w")
    for index,numbers in timers.iteritems():
        timerkey, timerno = index.rsplit("-")
        if not numbers[1]-numbers[0] < 0:
            outputfile.write("%s:\t%s\t%s\t%s\n"  % (str(timerno), str(numreplicas), str(numacceptors), str(numbers[1]-numbers[0])))
    outputfile.close()
