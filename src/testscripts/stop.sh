#!/bin/bash

HOSTFILE=./hosts

if [[ ! -f ${HOSTFILE} ]]
then
    echo "HOSTFILE doesn't exist".
    exit 1
fi

a=0
while read line
do a=$(($a+1));
machines[$a]=$line;
done < ${HOSTFILE}

for (( i = 1; i <= a; i++ ))
do
    echo ${machines[$i]}
    ssh ${machines[$i]} "killall -9 python &"
    ssh ${machines[$i]} "rm -rf /local/concoord-deniz/* &"
done
wait