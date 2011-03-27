rm -rf output
mkdir -p output

for run in {1..30}; do
    for numreplicas in {1..20}; do
	echo "run $run with $numreplicas replicas" 
	python replica.py | grep "^XXX" >> output/$numreplicas 2> /dev/null &
	sleep 5
	for acceptor in {1..4};do
	    python acceptor.py -b 127.0.0.1:6668 > /dev/null 2>&1 &
	done
	sleep 10
	for (( x=1; x<=$numreplicas; x++ )); do
	    python replica.py -b 127.0.0.1:6668 > /dev/null 2>&1 &
	done
	sleep 10
	python client.py -b 127.0.0.1:6668 < client1 > /dev/null 2>&1
	sleep 60
	killall python
	sleep 5
	killall -9 python
    done
done
