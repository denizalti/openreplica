#!/bin/sh

SLICENAME=cornell_openreplica

make clobber
make node

for var in "$@"
do
    echo "$var"
    scp -i openreplicakey -o StrictHostKeyChecking=no concoordnode.tar.gz $SLICENAME@$var:
    ssh -i openreplicakey -o StrictHostKeyChecking=no $SLICENAME@$var 'rm -rf bin; tar xzf concoordnode.tar.gz && rm concoordnode.tar.gz'
done