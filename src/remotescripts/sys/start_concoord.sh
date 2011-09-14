#!/bin/bash                                                                                          

BASE=/local/concoord-deniz
LOGFILE=${BASE}/concoord.log.${HOSTNAME}
CONCOORDR=/home/deniz/concoord/replica.py
CONCOORDA=/home/deniz/concoord/acceptor.py
CONCOORDC=/home/deniz/concoord/client.py
PYTHON=python

ulimit -c unlimited
cd ${BASE}

if [ ${HOSTNAME} = "sys15" ]; then
    nohup ${PYTHON} ${CONCOORDR} -o bank -d >> ${LOGFILE} 2>&1 &
elif [ ${HOSTNAME} = "sys04" ] || [ ${HOSTNAME} = "sys05" ] || [ ${HOSTNAME} = "sys07" ] || [ ${HOST\
NAME} = "sys08" ] || [ ${HOSTNAME} = "sys09" ]; then
    nohup ${PYTHON} ${CONCOORDA} -b 128.84.227.65:6668 -d >> ${LOGFILE} 2>&1 &
elif [ ${HOSTNAME} = "sys10" ] || [ ${HOSTNAME} = "sys11" ] || [ ${HOSTNAME} = "sys12" ] || [ ${HOST\
NAME} = "sys13" ] || [ ${HOSTNAME} = "sys14" ]; then
    nohup ${PYTHON} ${CONCOORDR} -b 128.84.227.65:6668 -d >> ${LOGFILE} 2>&1 &
elif [ ${HOSTNAME} = "sys01" ]; then
    nohup ${PYTHON} ${CONCOORDC} -b 128.84.227.65:6668 >> ${LOGFILE} 2>&1 &
fi
