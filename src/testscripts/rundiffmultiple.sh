#!/bin/bash

for (( i=40; i<=100; i+=10 )); do
    for (( j=70; j<=90; j+=10 )); do
	./start_test.rc $i $j
	echo $i " Replica " $j " Acceptor started."
	sleep 60
	./stop_test.rc
    done
done