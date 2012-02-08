#!/bin/sh

SLICENAME=cornell_openreplica

for var in "$@"
do
    echo "$var"
    ssh -i openreplicakey -o StrictHostKeyChecking=no $SLICENAME@$var 'killall -9 python'
done