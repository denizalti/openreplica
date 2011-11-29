#!/bin/sh

SLICENAME=cornell_openreplica
NODE=$1

ssh -i openreplicakey -o StrictHostKeyChecking=no $SLICENAME@$NODE "echo export SUDO_ASKPASS=/bin/true >> .bashrc"
ssh -i openreplicakey -o StrictHostKeyChecking=no $SLICENAME@$NODE "cat .bashrc"