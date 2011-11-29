#!/bin/sh

SLICENAME=cornell_openreplica
NODE=$1

ssh -i openreplicakey -o StrictHostKeyChecking=no $SLICENAME@$NODE 'export SUDO_ASKPASS=/bin/true && sudo -A sh -c "killall -9 python; rm concoord_log*"'