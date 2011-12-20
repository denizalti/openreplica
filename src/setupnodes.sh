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
    #scp -i openreplicakey -o StrictHostKeyChecking=no dnspython-1.9.4.tar.gz $SLICENAME@$var:
    #ssh -i openreplicakey -o StrictHostKeyChecking=no $SLICENAME@$var tar xzf dnspython-1.9.4.tar.gz
    #ssh -i openreplicakey -o StrictHostKeyChecking=no $SLICENAME@$var 'export SUDO_ASKPASS=/bin/true && sudo -A sh -c "cd dnspython-1.9.4; python setup.py install"'
done