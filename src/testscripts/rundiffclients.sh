#!/bin/bash

for (( i=10; i<=50; i+=5 )); do
    ./client_test.rc 5 5 $i
    echo $i " Clients started."
    sleep 200
    ./stop_test.rc
done