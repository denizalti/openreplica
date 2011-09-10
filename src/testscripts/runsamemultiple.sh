#!/bin/bash

ARGS=2
E_BADARGS=65

if [ $# -ne "$ARGS" ]
then
  echo "Usage: `basename $0` number-of-replicas number-of-acceptors"
  exit $E_BADARGS
fi

for (( i=1; i<3; i++ )); do
	./start_test.sh $1 $2
	echo "Run " $i
	sleep 400
	./stop_test.sh
	./clean_test.sh
done