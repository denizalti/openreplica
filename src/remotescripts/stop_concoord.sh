#!/bin/bash

BASE=/local/concoord-deniz
PIDFILE=${BASE}/concoord.pid

if [[ ! -f ${PIDFILE} ]]
then
    echo "ConCoord PIDFILE doesn't exist".
    exit 1
fi

kill -INT `cat ${PIDFILE}` || (echo "Failure to kill ConCoord." ; exit 1)
rm ${PIDFILE}
exit 0
