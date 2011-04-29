#!/bin/sh

ARGS=1
E_BADARGS=65

if [ $# -ne "$ARGS" ]
then
  echo "Usage: `basename $0` host"
  exit $E_BADARGS
fi

rm ./src/*.pyc
rm ./src/obj/*.pyc
tar -czvf  paxi.tar.gz src
scp ./paxi.tar.gz $1:
scp ./remoteinit.sh $1: