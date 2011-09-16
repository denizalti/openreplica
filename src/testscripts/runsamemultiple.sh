#!/bin/bash

ARGS=2
E_BADARGS=65

if [ $# -ne "$ARGS" ]
then
  echo "Usage: `basename $0` number-of-replicas number-of-acceptors"
  exit $E_BADARGS
fi

for (( i=1; i<10; i++ )); do
	./start_test.rc $1 $2
	echo "Run " $i
	sleep 100
	./stop_test.rc
done