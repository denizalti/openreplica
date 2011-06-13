#!/bin/sh

ARGS=1
E_BADARGS=65

if [ $# -ne "$ARGS" ]
then
  echo "Usage: `basename $0` host"
  exit $E_BADARGS
fi

ssh $1 screen -m -d "python ./paxi/replica.py -b 128.84.227.79:6668"
