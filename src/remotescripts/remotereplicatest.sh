#!/bin/sh
# This script starts a given number of replica nodes, 3 acceptor nodes
# and a client node on a remote sys server.

ARGS=1
E_BADARGS=65

if [ $# -ne "$ARGS" ]
then
  echo "Usage: `basename $0` number-of-replicas"
  exit $E_BADARGS
fi
# REPLICA_0: sys01
# ACCEPTOR_0: sys03
 
# ACCEPTORS: sys04-05
# REPLICAS: sys06+

let "numreplicas = $2 + 4"

./remotestartlogreplica.sh sys01 $numreplicas
sleep 1
./remotestartacceptor.sh sys03
sleep 1
./remotestartacceptor.sh sys04
./remotestartacceptor.sh sys05

let "numreplicastest = $numreplicas - 10"

if [ $numreplicastest -lt "0" ]
then
    for (( x=6; x<=$numreplicas; x++ )); do
	./remotestartreplica.sh "sys0$x"
    done
else
    for (( x=6; x<="10"; x++ )); do
	./remotestartreplica.sh "sys0$x" 
    done
    for (( x=0; x<=$numreplicastest; x++ )); do
	./remotestartreplica.sh "sys1$x" 
    done
fi

./remotestartclient.sh sys15
