#!/bin/sh

SLICENAME=cornell_openreplica

for var in "$@"
do
    echo "$var"
    ssh -i ../secret/openreplicaplkey -o StrictHostKeyChecking=no $SLICENAME@$var 'sudo killall -9 python2.7'
done