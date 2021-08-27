#!/bin/bash

NUM_CLIENTS=1

counter=1
while [ $counter -le $NUM_CLIENTS ]
do
	echo "mla4EVER" | sudo -S /usr/local/sbin/sstpc --log-level 3 --log-stderr --cert-warn --user user --password \
	'password' 10.0.0.240:443 usepeerdns require-pap noipdefault nodefaultroute &
	((counter++))
done

sleep 8

# # Run iperf3 as a client to communicate with the IP address that runs
# # the iperf3 server (which is 10.0.0.241). The server would run iperf3 in server mode.
# # If we connect N number of client, we must create N number of server!
# # We must bind each client to a specific interface for testing.
# # Interface IP starts from 192.168.20.2 and increases by one for each client.
IP_BASE=192.168.20.
ip_suffix=2
base_server_port=5101 # This must be the same between the server and the client!
counter=1

#while [ $counter -le $NUM_CLIENTS ] # NUM_SERVERS == NUM_CLIENTS!
#do
#  IP=${IP_BASE}${ip_suffix}
#  server_port=$((base_server_port+counter))
#  /Users/mvanbastelaer/Documents/harvard/g5/splice/iperf3 -c 10.0.0.241 -p ${server_port} -B ${IP} --cport 8080 --logfile ./${IP}.txt &
#  ((ip_suffix++))
#  ((counter++))
#done

# # Apache Benchmark (ab): No need to bind the interface through iptable.
# # At the client side run:
# # ab -n 100 -c 1 -B 192.168.20.2 https://10.0.0.241/
# # Where -B does the binding automatically.

NUM_REQUESTS=500  # Number of requests to perform
CONCURRENCY=5     # Number of multiple requests to make at a time
while [ $counter -le $NUM_CLIENTS ]
do
  IP=${IP_BASE}${ip_suffix}
  ab -n ${NUM_REQUESTS} -c ${CONCURRENCY} -B ${IP} https://10.0.0.241/ > ./${IP}.txt &
  ((ip_suffix++))
  ((counter++))
done
