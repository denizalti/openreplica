#!/bin/bash

# This script starts a given number of replica nodes, and acceptor nodes
# and a client node on sys cluster.

ARGS=2
E_BADARGS=65

if [ $# -ne "$ARGS" ]
then
  echo "Usage: `basename $0` number-of-replicas number-of-acceptors"
  exit $E_BADARGS
fi

# REPLICA_0: cfs29
# ACCEPTORS: cfs30-34
# REPLICAS: cfs35-39
# CLIENT: cfs28

let "numreplicas = $1 - 1"
let "numacceptors = $2"

ssh "deniz@cfs29.cs.cornell.edu" ./start_concoord.sh
echo "cfs29"
sleep 2

for (( x=0; x<$numreplicas; x++ )); do
    let "i = x % 5"
    ssh "deniz@cfs3$i.cs.cornell.edu" ./start_concoord.sh
    echo "cfs3$i"
done
sleep 2

for (( x=0; x<$numacceptors; x++ )); do
    let "i = x % 5"
    let "i = i+5"
    ssh "deniz@cfs3$i.cs.cornell.edu" ./start_concoord.sh
    echo "cfs3$i"
done
sleep 5

ssh "deniz@cfs28.cs.cornell.edu" ./start_concoord.sh
echo "cfs28"
