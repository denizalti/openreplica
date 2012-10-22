#!/bin/sh

killall -9 python
cd /var/www/concoord/src/ && python setup.py install
cd /var/www/concoord/src/concoord && python replica.py -f nameservercoord.py -c NameserverCoord -p 14000 &
cd /var/www/concoord/src/concoord && python acceptor.py -b 128.84.154.110:14000 &
cd /var/www/concoord/src/concoord && python openreplica/openreplicanameserver.py -f nameservercoord.py -c NameserverCoord -b 128.84.154.110:14000 -t 1 &
