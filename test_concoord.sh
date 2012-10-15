#!/bin/sh

killall -9 python
cd src/ && python setup.py install
cd concoord/ && python replica.py -f test_object.py -c Value -p 14000 -a localhost&
cd concoord/ && python acceptor.py -b localhost:14000 &
cd concoord/ && python nameserver.py -f test_object.py -c Value -n www.test.com -b localhost:14000 -t 1 &
sleep 2
cd concoord/ && python test_client.py -b localhost:14000