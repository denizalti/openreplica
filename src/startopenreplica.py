'''
@author: deniz
@note: Starts OpenReplica
@date: January 30, 2011
'''
import random
import os, sys, time, shutil
import ast, _ast
import subprocess

def executecommandone(node, command, username='cornell_openreplica', keyfile='openreplicakey'):
    cmd = ["ssh", "-i", keyfile, "-o", "StrictHostKeyChecking=no", username + "@" + node, command]
    print "Executing: %s" % cmd
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc

def executelocal(cmd):
    print "Executing: %s" % cmd
    proc =  subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc

def start_nodes():
    # locate the right number of suitable PlanetLab nodes
    clientobjectfilename = 'openreplicacoordobj.py'
    classname = 'OpenReplicaCoord'
    replicas =  ['128.84.154.110', '128.232.103.201', '128.112.139.43', '128.208.4.197', '139.19.142.2']
    acceptors =  ['128.84.154.110', '128.232.103.201', '128.112.139.43', '128.208.4.197', '139.19.142.2']
    nameservers = ['128.84.154.110', '128.232.103.201', '128.112.139.43', '128.208.4.197', '139.19.142.2']
    allnodes = replicas + acceptors + nameservers
    print "=== Nodes ==="
    for node in allnodes:
        print node
    print "--> Setting up the environment..."
    # EGS-110 HOSTS
    print "--- egs-110 hosts ---"
    port = 6700
    p = executelocal("nohup python /var/www/concoord/src/replica.py -a %s -p %d -f %s -c %s" % (replicas[0], port, clientobjectfilename, classname))
    while terminated(p):
        port = random.randint(14000, 15000)
        p = executelocal("nohup python /var/www/concoord/src/replica.py -a %s -p %d -f %s -c %s" % (replicas[0], port, clientobjectfilename, classname))
    bootstrapname = replicas[0]+':'+str(port)
    print bootstrapname
    # ACCEPTOR on egs-110
    port = 6800
    p = executelocal("nohup python /var/www/concoord/src/acceptor.py -a %s -p %d -f %s -b %s" % (acceptors[0], port, clientobjectfilename, bootstrapname))
    while terminated(p):
        port = random.randint(14000, 15000)
        p = executelocal("nohup python /var/www/concoord/src/acceptor.py -a %s -p %d -f %s -b %s" % (acceptors[0], port, clientobjectfilename, bootstrapname))
    acceptorname = acceptors[0]+':'+str(port)
    print acceptorname
    # NAMESERVER on egs-110
    port = random.randint(14000, 15000)
    p = executelocal("sudo -A nohup python /var/www/concoord/src/openreplicanameserver.py -a %s -p %d -f %s -c %s -b %s" % (nameservers[0], port, clientobjectfilename, classname, bootstrapname))
    while terminated(p):
        print "Trying again..."
        port = random.randint(14000, 15000)
        p = executelocal("sudo -A nohup python /var/www/concoord/src/openreplicanameserver.py -a %s -p %d -f %s -c %s -b %s" % (nameservers[0], port, clientobjectfilename, classname, bootstrapname))
    nameservername = nameservers[0]+':'+str(port)
    print nameservername
    time.sleep(5)
    # ACCEPTORS
    bootstrapname = 'openreplica.org'
    print "--- Acceptors ---"
    for acceptor in acceptors[1:]:
        port = random.randint(14000, 15000)
        p = executecommandone(acceptor, "nohup /home/cornell_openreplica/python2.7/bin/python2.7 bin/acceptor.py -a %s -p %d -f %s -b %s" % (acceptor, port, clientobjectfilename, bootstrapname))
        while terminated(p):
            port = random.randint(14000, 15000)
            p = executecommandone(acceptor, "nohup /home/cornell_openreplica/python2.7/bin/python2.7 bin/acceptor.py -a %s -p %d -f %s -b %s" % (acceptor, port, clientobjectfilename, bootstrapname))
        acceptorname = acceptor+':'+str(port)
        processnames.append(acceptorname)
        print acceptorname
    # REPLICAS
    if numreplicas-1 > 0:
        print "--- Replicas ---"
    for replica in replicas[1:]:
        port = random.randint(14000, 15000)
        p = executecommandone(replica, "nohup /home/cornell_openreplica/python2.7/bin/python2.7 bin/replica.py -a %s -p %d -f %s -c %s -b %s" % (replica, port, clientobjectfilename, classname, bootstrapname))
        while terminated(p):
            port = random.randint(14000, 15000)
            p = executecommandone(replica, "nohup /home/cornell_openreplica/python2.7/bin/python2.7 bin/replica.py -a %s -p %d -f %s -c %s -b %s" % (replica, port, clientobjectfilename, classname, bootstrapname))
        replicaname = replica+':'+str(port)
        processnames.append(replicaname)
        print replicaname
    # NAMESERVERS
    print "--- Nameservers ---"
    for nameserver in nameservers[1:]:
        port = random.randint(14000, 15000)
        p = executecommandone(nameserver, "sudo -A nohup /home/cornell_openreplica/python2.7/bin/python2.7 bin/openreplicanameserver.py -a %s -p %d -f %s -c %s -b %s" % (nameserver, port, clientobjectfilename, classname, bootstrapname))
        while terminated(p):
            port = random.randint(14000, 15000)
            p = executecommandone(nameserver, "sudo -A nohup /home/cornell_openreplica/python2.7/bin/python2.7 bin/openreplicanameserver.py -a %s -p %d -f %s -c %s -b %s" % (nameserver, port, clientobjectfilename, classname, bootstrapname))
        nameservername = nameserver+':'+str(port)
        processnames.append(nameservername)
        nameservernames.append(nameservername)
        print nameservername
    print "All clear!"

def terminated(p):
    i = 5
    done = p.poll() is not None
    while not done and i>0: # Not terminated yet
        time.sleep(1)
        i -= 1
        done = p.poll() is not None
    return done

def main():
    try:
        start_nodes()
    except Exception as e:
        print "Error: ", e
    
if __name__=='__main__':
    main()
