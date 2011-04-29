#!/bin/sh

ARGS=2
E_BADARGS=65

if [ $# -ne "$ARGS" ]
then
  echo "Usage: `basename $0` number-of-acceptors number-of-replicas"
  exit $E_BADARGS
fi

let "numacceptors = $1 - 1"
let "numreplicas = $2 - 1"

rm ports

tmux rename main
unset TMUX
tmux kill-session -t paxi
tmux new-session -d -s paxi

tmux new-window -t paxi:1 -n 'Replica 0' 'python replica.py -l'
sleep 1
tmux new-window -t paxi:2 -n 'NameServer' 'sudo python nameserver.py -l -b 127.0.0.1:6668'
sleep 1
tmux new-window -t paxi:3 -n 'Acceptor 0' 'python acceptor.py -l -b 127.0.0.1:6668'
sleep 1
tmux new-window -t paxi:4 -n 'Replicas' "bash startreplicas.sh \"$numreplicas\""
tmux new-window -t paxi:5 -n 'Acceptors' "bash startacceptors.sh \"$numacceptors\""
tmux new-window -t paxi:6 -n 'Client' 'python client.py -b 127.0.0.1:6668 -f ports'
tmux switch -t paxi