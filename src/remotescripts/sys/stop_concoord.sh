#!/bin/bash                                                                                          

BASE=/local/concoord-deniz

a=0
while read line
do a=$(($a+1));
processes[$a]=$line;
done < ${PIDFILE}

for (( i = 1; i <= a; i++ ))
do
    kill -9 ${processes[$i]} || echo "Failure to kill ConCoord."
done
exit 0

