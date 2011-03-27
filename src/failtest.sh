rm -rf output
mkdir -p output

for run in {1..30}; do
	echo "run $run" 
	python replica.py | grep "^XXX" >> output/failtest 2> /dev/null &
	sleep 5
	for acceptor in {1..4};do
	    python acceptor.py -b 127.0.0.1:6668 > /dev/null 2>&1 &
	done
	sleep 10
	for replica in {1..4};do
	    python replica.py -b 127.0.0.1:6668 | grep "^XXX" >> output/failtest 2> /dev/null &
	done
	sleep 10
	python client.py -b 127.0.0.1:6668 < client1 > /dev/null 2>&1
	sleep 3
	kill %1
	sleep 57
	killall python
	sleep 5
	killall -9 python
done
