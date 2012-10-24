#!/bin/sh

killall -9 python
cd /var/www/concoord/src/ && python setup.py install
cd /var/www/concoord/src/concoord && python replica.py -f nameservercoord.py -c NameserverCoord -b openreplica.org -p 14000 &
cd /var/www/concoord/src/concoord && python acceptor.py -b openreplica.org &
cd /var/www/concoord/src/concoord && python openreplica/openreplicanameserver.py -f nameservercoord.py -c NameserverCoord -b openreplica.org -t 1 &
