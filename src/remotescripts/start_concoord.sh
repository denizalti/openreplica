#!/bin/bash

BASE=/local/concoord-deniz
LOGFILE=${BASE}/concoord.log.${HOSTNAME}
PIDFILE=${BASE}/concoord.pid
CONCOORDR=/home/deniz/concoord/replica.py
CONCOORDA=/home/deniz/concoord/acceptor.py
CONCOORDC=/home/deniz/concoord/client.py
PYTHON=python

if [[ -f ${PIDFILE} ]]
then
	echo "ConCoord already running (or stale PIDFILE)"
	exit 1
fi

ulimit -c unlimited
cd ${BASE}

if [ ${HOSTNAME} = "sys01" ]; then
    nohup ${PYTHON} ${CONCOORDR} -o bank >> ${LOGFILE} 2>&1 &
elif [ ${HOSTNAME} = "sys04" ] || [ ${HOSTNAME} = "sys05" ] || [ ${HOSTNAME} = "sys07" ] || [ ${HOSTNAME} = "sys08" ] || [ ${HOSTNAME} = "sys09" ]; then 
    nohup ${PYTHON} ${CONCOORDA} -b 128.84.227.79:6668 >> ${LOGFILE} 2>&1 &
elif [ ${HOSTNAME} = "sys10" ] || [ ${HOSTNAME} = "sys11" ] || [ ${HOSTNAME} = "sys12" ] || [ ${HOSTNAME} = "sys13" ] || [ ${HOSTNAME} = "sys14" ]; then 
    nohup ${PYTHON} ${CONCOORDR} -b 128.84.227.79:6668 >> ${LOGFILE} 2>&1 &
elif [ ${HOSTNAME} = "sys15" ]; then
    nohup ${PYTHON} ${CONCOORDC} -o bank >> ${LOGFILE} 2>&1 &
fi

echo $! > ${PIDFILE}