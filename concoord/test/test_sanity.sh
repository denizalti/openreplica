#!/bin/sh

killall -9 python
concoord replica -o concoord.test.test_sanity.TestSanity -p 14000 -a 127.0.0.1 &
concoord acceptor -b 127.0.0.1:14000 &
concoord nameserver -o concoord.test.test_sanity.TestSanity -n www.test.com -b 127.0.0.1:14000 -t 1 &
sleep 2
python test_sanity_client.py -b 127.0.0.1:14000