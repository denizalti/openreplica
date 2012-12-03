#!/bin/sh

SLICENAME=cornell_openreplica

for var in "$@"
do
    echo "$var"
    ssh -i ../secret/openreplicaplkey -o StrictHostKeyChecking=no $SLICENAME@$var 'rm -rf concoord*'
    scp -i ../secret/openreplicaplkey -o StrictHostKeyChecking=no ../src/dist/concoord-0.9.0.tar.gz $SLICENAME@$var:
    ssh -i ../secret/openreplicaplkey -o StrictHostKeyChecking=no $SLICENAME@$var 'tar xzvf concoord-0.9.0.tar.gz && rm concoord-0.9.0.tar.gz'
    ssh -i ../secret/openreplicaplkey -o StrictHostKeyChecking=no $SLICENAME@$var 'cd concoord-0.9.0/ && /home/cornell_openreplica/python2.7/bin/python2.7 setup.py install'
done