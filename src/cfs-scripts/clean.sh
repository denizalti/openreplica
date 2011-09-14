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
    ssh ${machines[$i]} ./clean_concoord.sh
done