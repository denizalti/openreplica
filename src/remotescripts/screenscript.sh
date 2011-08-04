#!/bin/sh

ARGS=1
E_BADARGS=65

if [ $# -ne "$ARGS" ]
then
  echo "Usage: `basename $0` host"
  exit $E_BADARGS
fi

ssh $1 "rm -rf ./paxi/output"
ssh $1 "mkdir ./paxi/output"
ssh $1 screen -m -d "which ls > ./paxi/output/test2"