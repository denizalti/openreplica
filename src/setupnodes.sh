#!/bin/sh

SLICENAME=cornell_openreplica
NODE=$1

scp -i openreplicakey -o StrictHostKeyChecking=no concoord.tar.gz $SLICENAME@$NODE:
#scp -i openreplicakey -o StrictHostKeyChecking=no dnspython-1.9.4.tar.gz $SLICENAME@$NODE:
ssh -i openreplicakey -o StrictHostKeyChecking=no $SLICENAME@$NODE rm -r bin
ssh -i openreplicakey -o StrictHostKeyChecking=no $SLICENAME@$NODE mkdir bin
ssh -i openreplicakey -o StrictHostKeyChecking=no $SLICENAME@$NODE tar xzf concoord.tar.gz -C bin
#ssh -i openreplicakey -o StrictHostKeyChecking=no $SLICENAME@$NODE tar xzf dnspython-1.9.4.tar.gz
#ssh -i openreplicakey -o StrictHostKeyChecking=no $SLICENAME@$NODE 'export SUDO_ASKPASS=/bin/true && sudo -A sh -c "cd dnspython-1.9.4; python setup.py install"'