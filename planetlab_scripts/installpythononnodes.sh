#!/bin/sh

SLICENAME=cornell_openreplica

for var in "$@"
do
    echo "$var"
    scp -i ../secret/openreplicaplkey -o StrictHostKeyChecking=no python2.7.tar.gz $SLICENAME@$var:
    ssh -i ../secret/openreplicaplkey -o StrictHostKeyChecking=no $SLICENAME@$var 'tar xzf python2.7.tar.gz || rm python2.7.tar.gz'
done