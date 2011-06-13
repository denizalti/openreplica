#!/bin/sh

ARGS=2
E_BADARGS=65

if [ $# -ne "$ARGS" ]
then
  echo "Usage: `basename $0` host number-of-replicas"
  exit $E_BADARGS
fi

ssh $1 "rm -rf ./paxi/output"
ssh $1 "mkdir ./paxi/output"
ssh $1 screen -m -d "python ./paxi/replica.py | grep '^YYY' >> ./paxi/output/$2"
