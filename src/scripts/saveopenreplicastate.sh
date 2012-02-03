#!/bin/sh
if test $# -ne 1; then
    echo Usage: logmanage filename
    exit 1
fi
FILE=$1
NEWFILE="$FILE.new"
python saveopenreplicastate.py > $FILE.new
if ! cmp -s $NEWFILE $FILE; then
    NEWNAME=`echo $FILE.\`date '+%Y-%m-%d-%H:%M.%S'\`.log`
    mv -f $NEWFILE $NEWNAME && ln -f $NEWNAME $FILE
fi