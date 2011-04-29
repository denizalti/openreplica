# Argument check
ARGS=3
E_BADARGS=65

if [ $# -gt "$ARGS" -o $# -eq 0 ]
then
  echo "Usage: `basename $0` number-of-acceptors [bootstrap: addr:port]"
  exit $E_BADARGS
fi

for (( x=1; x<=$1; x++ )); do
    if [ $# -eq "1" ]
    then
	python acceptor.py < /dev/null &
    else
	python acceptor.py -b $2< /dev/null &
    fi
done

wait
