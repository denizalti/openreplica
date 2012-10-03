#!/bin/sh

killall -9 python
cd ~/projects/concoord/src/ && python setup.py install
cd ~/projects/concoord/src/concoord && python replica.py -f test_object.py -c Value -p 14000 -a localhost&
cd ~/projects/concoord/src/concoord && python acceptor.py -b localhost:14000 &
cd ~/projects/concoord/src/concoord && python nameserver.py -f test_object.py -c Value -n www.test.com -b localhost:14000 -t 1 &
#cd ~/projects/concoord/src/concoord && python test_client.py -b localhost:14000