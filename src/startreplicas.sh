# Argument check
ARGS=1
E_BADARGS=65

if [ $# -ne "$ARGS" ]
then
  echo "Usage: `basename $0` number-of-replicas"
  exit $E_BADARGS
fi

for (( x=1; x<=$1; x++ )); do
    python replica.py -l < /dev/null & 
done

wait
