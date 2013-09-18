'''
@author: Deniz Altinbuken, Emin Gun Sirer
@note: Utility functions for the runtime. Includes a timer module for collecting measurements.
@copyright: See LICENSE
'''
import socket
import os, sys
import time
import string
import threading
from concoord.enums import *

def findOwnIP():
    """Retrieves the hostname of the caller"""
    return socket.gethostbyname(socket.gethostname())

def load_configdict(configpath):
    configfile = os.path.basename(configpath)
    configdir = os.path.dirname(configpath)
    sys.path.append(configdir)
    configmodule = __import__(configfile[:-3], globals(), locals(), [], -1)
    config_dict = {}
    for key in dir(configmodule):
        if key.startswith('__'):
            continue
        else:
            config_dict[key] = getattr(configmodule, key)
    return config_dict

def get_addressportpairs(group):
    for peer in group.iterkeys():
        yield (peer.addr,peer.port)

def get_addresses(group):
    for peer in group.iterkeys():
        yield peer.addr

# A logger will always print to the screen. It can also log to a file or to a network log daemon.
class NoneLogger():
    def write(self, cls, string):
        return

    def close(self):
        return

class Logger():
    def __init__(self, name, filename=None, lognode=None):
        self.prefix = name
        self.log = None
        if filename is not None:
            self.log = open("concoord_log_"+name, 'w')
        if lognode is not None:
            logaddr,logport = lognode.split(':')
            try:
                self.log = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                self.log.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                self.log.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
                self.log.connect((logaddr,int(logport)))
            except IOError:
                self.log = None
                return

    def write(self, cls, string):
        print "[%s] %s %s: %s" % (self.prefix + '_' + threading.current_thread().name,
                                  time.time(), # time.asctime(time.localtime(time.time())),
                                  cls, string)
        if self.log is not None:
            self.log.write("[%s] %s %s: %s" % (self.prefix + '_' + threading.current_thread().name,
                                               time.time(), # time.asctime(time.localtime(time.time())),
                                               cls, string))
            self.log.flush()

    def close(self):
        if self.log is not None:
            self.log.close()

# PERFORMANCE MEASUREMENT UTILS
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

def dumptimers(numreplicas, numacceptors, ownertype, outputdict):
    global timers
    if ownertype == NODE_REPLICA:
        filename = "output/replica/%s-%s" % (str(numreplicas), str(numacceptors))
    elif ownertype == NODE_ACCEPTOR:
        filename = "output/acceptor/%s-%s" % (str(numreplicas), str(numacceptors))
    try:
        outputfile = open(outputdict+filename, "w")
    except:
        outputfile = open("./"+filename, "w")
    for index,numbers in timers.iteritems():
        timerkey, timerno = index.rsplit("-")
        if not numbers[1]-numbers[0] < 0:
            outputfile.write("%s:\t%s\t%s\t%s\n"  % (str(timerno),
                                                     str(numreplicas),
                                                     str(numacceptors),
                                                     str(numbers[1]-numbers[0])))
    outputfile.close()

def starttiming(fn):
    """
    Decorator used to start timing.
    Keeps track of the count for the first and second calls.
    """
    def new(*args, **kw):
        obj = args[0]
        if obj.firststarttime == 0:
            obj.firststarttime = time.time()
        elif obj.secondstarttime == 0:
            obj.secondstarttime = time.time()
        profile_on()
        return fn(*args, **kw)
    return new

def endtiming(fn):
    """
    Decorator used to end timing.
    Keeps track of the count for the first and second calls.
    """
    NITER = 10000
    def new(*args, **kw):
        ret = fn(*args, **kw)
        obj = args[0]
        if obj.firststoptime == 0:
            obj.firststoptime = time.time()
        elif obj.secondstoptime == 0:
            obj.secondstoptime = time.time()
        elif obj.count == NITER:
            now = time.time()
            total = now - obj.secondstarttime
            perrequest = total/NITER
            filename = "output/%s-%s" % (str(len(obj.groups[NODE_REPLICA])+1),
                                         str(len(obj.groups[NODE_ACCEPTOR])))
            outputfile = open("./"+filename, "a")
            # numreplicas #numacceptors #perrequest #total
            outputfile.write("%s\t%s\t%s\t%s\n" % (str(len(obj.groups[NODE_REPLICA])+1),
                                                   str(len(obj.groups[NODE_ACCEPTOR])),
                                                   str(perrequest), str(total)))
            outputfile.close()
            obj.count += 1
            sys.stdout.flush()
            profile_off()
            profilerdict = get_profile_stats()
            for key, value in sorted(profilerdict.iteritems(),
                                     key=lambda (k,v): (v[2],k)):
                print "%s: %s" % (key, value)
            time.sleep(10)
            sys.stdout.flush()
            os._exit(0)
        else:
            obj.count += 1
        return ret
    return new

def throughput_test(fn):
    """Decorator used to measure throughput."""
    def new(*args, **kw):
        ret = fn(*args, **kw)
        obj = args[0]
        obj.throughput_runs += 1
        if obj.throughput_runs == 100:
            obj.throughput_start = time.time()
        elif obj.throughput_runs == 1100:
            obj.throughput_stop = time.time()
            totaltime = obj.throughput_stop - obj.throughput_start
            print "********************************************"
            print "TOTAL: ", totaltime
            print "TPUT: ", 1000/totaltime, "req/s"
            print "********************************************"
            obj._graceexit(1)
        return ret
    return new

