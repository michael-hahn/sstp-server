#!/bin/bash
# RUN MULTIPLE SSTP CLIENTS ON DOCKER
# Check out client.sh for basic setup first!
NUM_CLIENTS=1
IP_BASE=172.19.0.
ip_suffix=3

counter=1
while [ $counter -le $NUM_CLIENTS ]
do
  IP=${IP_BASE}${ip_suffix}
  docker run -d --rm --cpuset-cpus="2" --privileged --network client --ip=${IP} --name=sstp-client-${counter} sstp-client
	((counter++))
	((ip_suffix++))
done
