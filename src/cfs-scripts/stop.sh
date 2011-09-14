#!/bin/bash

RUNFILE=./runningon

if [[ ! -f ${RUNFILE} ]]
then
    echo "ConCoord RUNFILE doesn't exist".
    exit 1
fi

a=0
while read line
do a=$(($a+1));
machines[$a]=$line;
done < ${RUNFILE}

for (( i = 1; i <= a; i++ ))
do
    ssh ${machines[$i]} ./stop_concoord.sh
done