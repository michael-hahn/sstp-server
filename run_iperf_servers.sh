#!/bin/bash
# RUN MULTIPLE IPERF SERVERS ON DOCKER
# Check out server.sh for basic setup first!
# NUM_SERVERS should be the same as NUM_CLIENTS in run_iperf_clients.sh
NUM_SERVERS=1
# IP_BASE and ip_suffix are the IP of iperf3 servers.
# Each iperf3 server talks to a separate iperf3 client.
IP_BASE=172.18.0.
ip_suffix=3

counter=1
while [ $counter -le $NUM_SERVERS ]
do
  IP=${IP_BASE}${ip_suffix}
  # Should pin to a different set of CPU as iperf clients
	docker run -d --rm --cpuset-cpus="3" --name=iperf-server-${counter} --network=server --ip=${IP} networkstatic/iperf3 -s
	((counter++))
	((ip_suffix++))
done
