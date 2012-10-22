#!/bin/sh

nohup /home/cornell_openreplica/python2.7/bin/python2.7 concoord-0.3.0/concoord/replica.py -a 128.208.4.197 -p 14006 -f nameservercoord.py -c NameserverCoord -b 128.84.154.110:14000 &

nohup /home/cornell_openreplica/python2.7/bin/python2.7 concoord-0.3.0/concoord/acceptor.py -a 128.208.4.197 -p 14007 -b 128.84.154.110:14000 &

sudo nohup /home/cornell_openreplica/python2.7/bin/python2.7 concoord-0.3.0/concoord/openreplica/openreplicanameserver.py -a 128.208.4.197 -p 14008 -f nameservercoord.py -c NameserverCoord -b 128.84.154.110:14000 -t 1 &
