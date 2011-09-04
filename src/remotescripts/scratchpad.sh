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
rm ${RUNFILE}

let "numreplicas = $1 - 1"
let "numacceptors = $2"

echo sys01 >> ${RUNFILE}

for (( x=0; x<$numreplicas; x++ )); do
    let "i = x % 5"
    echo "sys1$i" >> ${RUNFILE}
done

for (( x=0; x<$numacceptors; x++ )); do
    let "i = x % 5"
    echo $i
    if [ $i -lt "2" ]
    then
	let "i = i+4"
    else
	let "i = i+5"
    fi
    echo "sys0$i"
    echo "sys0$i" >> ${RUNFILE}
done

echo sys15 >> ${RUNFILE}
