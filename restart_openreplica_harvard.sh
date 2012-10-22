#!/bin/sh

nohup /home/cornell_openreplica/python2.7/bin/python2.7 concoord-0.3.0/concoord/replica.py -a 140.247.60.126 -p 14009 -f nameservercoord.py -c NameserverCoord -b 128.84.154.110:14000 &

nohup /home/cornell_openreplica/python2.7/bin/python2.7 concoord-0.3.0/concoord/acceptor.py -a 140.247.60.126 -p 14010 -b 128.84.154.110:14000 &

sudo nohup /home/cornell_openreplica/python2.7/bin/python2.7 concoord-0.3.0/concoord/openreplica/openreplicanameserver.py -a 140.247.60.126 -p 14011 -f nameservercoord.py -c NameserverCoord -b 128.84.154.110:14000 -t 1 &
