#!/bin/sh

killall -9 python
cd ~/projects/concoord/src/ && python setup.py install
cd ~/projects/concoord/src/concoord && nohup python replica.py -f test_object.py -c Value -p 14000 -a localhost&
cd ~/projects/concoord/src/concoord && nohup python acceptor.py -b localhost:14000 &
cd ~/projects/concoord/src/concoord && nohup python nameserver.py -f test_object.py -c Value -b localhost:14000 -t 1 &
