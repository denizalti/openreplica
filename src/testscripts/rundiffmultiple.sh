#!/bin/bash

for (( i=10; i<=100; i+=10 )); do
    for (( j=10; j<=100; j+=10 )); do
	./start_test.rc $i $j
	echo $i " Replica " $j " Acceptor started."
	sleep 100
	./stop_test.rc
    done
done