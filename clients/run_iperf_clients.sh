#!/bin/bash
# RUN MULTIPLE IPERF CLIENTS ON DOCKER
# Check out client.sh for basic setup first!
# Run run_sstp_clients.sh first to set up SSTP clients.
# Each iperf client must be attached to one SSTP client.
NUM_CLIENTS=1
# IP_BASE and ip_suffix are the IP of iperf3 servers.
# Each iperf3 client talks to a separate iperf3 server.
IP_BASE=172.18.0.
ip_suffix=3

counter=1
while [ $counter -le $NUM_CLIENTS ]
do
  IP=${IP_BASE}${ip_suffix}
  # Should pin to the same set of CPU as SSTP clients
  # Mount FS so that we can get log data from the host machine
  # Ref: https://docs.docker.com/storage/bind-mounts/
	docker run -d --rm --cpuset-cpus="2" --net=container:sstp-client-${counter} --mount type=bind,source="$(pwd)",target=/var networkstatic/iperf3 -c ${IP} --logfile /var/${IP}.log
	((counter++))
	((ip_suffix++))
done
