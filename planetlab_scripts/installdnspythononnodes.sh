#!/bin/sh

SLICENAME=cornell_openreplica

for var in "$@"
do
    echo "$var"
    scp -i ../secret/openreplicaplkey -o StrictHostKeyChecking=no dnspython-1.9.4.tar.gz $SLICENAME@$var:
    ssh -i ../secret/openreplicaplkey -o StrictHostKeyChecking=no $SLICENAME@$var 'tar xzf dnspython-1.9.4.tar.gz && cd dnspython-1.9.4 && python setup.py install && rm dnspython-1.9.4.tar.gz'
done