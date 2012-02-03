#!/bin/sh

SLICENAME=cornell_openreplica

make clean
make

for var in "$@"
do
    echo "$var"
    scp -i openreplicakey -o StrictHostKeyChecking=no concoord.tar.gz $SLICENAME@$var:
    ssh -i openreplicakey -o StrictHostKeyChecking=no $SLICENAME@$var rm -r bin
    ssh -i openreplicakey -o StrictHostKeyChecking=no $SLICENAME@$var mkdir bin
    ssh -i openreplicakey -o StrictHostKeyChecking=no $SLICENAME@$var tar xzf concoord.tar.gz -C bin
    ssh -i openreplicakey -o StrictHostKeyChecking=no $SLICENAME@$var rm concoord.tar.gz
done