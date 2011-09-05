#!/bin/bash

#!/bin/sh
# This script starts a given number of replica nodes, 3 acceptor nodes
# and a client node on a remote sys server.

ARGS=2
E_BADARGS=65

if [ $# -ne "$ARGS" ]
then
  echo "Usage: `basename $0` number-of-replicas number-of-acceptors"
  exit $E_BADARGS
fi

RUNFILE=./runningon

# REPLICA_0: sys15
# ACCEPTORS: sys04, 05, 07, 08, 09
# REPLICAS: sys10, 11, 12, 13, 14
# CLIENT: sys01

let "numreplicas = $1 - 1"
let "numacceptors = $2"

ssh sys15 ./start_concoord.sh
echo sys15 >> ${RUNFILE}
sleep 2

for (( x=0; x<$numreplicas; x++ )); do
    let "i = x % 5"
    ssh "sys1$i" ./start_concoord.sh
    echo "sys1$i" >> ${RUNFILE}
done
sleep 2

for (( x=0; x<$numacceptors; x++ )); do
    let "i = x % 5"
    if [ $i -lt "2" ]
    then
	let "i = i+4"
    else
	let "i = i+5"
    fi
    ssh "sys0$i" ./start_concoord.sh
    echo "sys0$i" >> ${RUNFILE}
done
sleep 5

ssh sys01 ./start_concoord.sh
echo sys01 >> ${RUNFILE}
