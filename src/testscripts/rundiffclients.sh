#!/bin/bash

for (( i=10; i<=100; i+=10 )); do
    ./client_test.rc 5 5 $i
    echo $i " Clients started."
    sleep 300
    ./stop_test.rc
done