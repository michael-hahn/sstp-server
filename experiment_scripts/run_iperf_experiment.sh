#!/bin/bash

# This script runs the entire iperf3 experiment pipeline, including setting up the docker networks, the SSTP server,
# one or more SSTP clients, one or more iperf3 servers, and one or more iperf3 clients. You can find some of the
# commands used in this script from run_iperf_servers.sh, server.sh, run_sstp_clients.sh, and run_iperf_clients.sh.
# This script assumes that all docker images used in this script have been built successfully (and named
# correspondingly as indicated in this script).
# This script does *not* contain code to clean up after the experiment is finished.

# This script takes a number of flags:
# -s: if set, the SSTP-server is running with SPLICE (default is false)
# -n NUM_CLIENTS: number of SSTP clients (which is the same number of iperf3 clients and iperf3 servers)
# Parse the flags
WITH_SPLICE='false'
while getopts s:n: flag
do
  case "${flag}" in
    s) WITH_SPLICE='true';;
    n) NUM_CLIENTS=${OPTARG};;
    *) echo "UNKNOWN OPTION --> ${OPTKEY}" >&2
       exit 1;;
  esac
done

# Create the 'client' and the 'server' network. You do not need the --driver bridge flag since it’s the default,
# but this example shows how to specify it.
echo "[STATUS] setting up docker bridge networks only if they do not exist already..."
if [ -z $(docker network ls --filter name=^client$ --format="{{ .Name }}") ] ; then
  echo "[STATUS] 'client' network does not exist, setting it up now..."
  docker network create --driver bridge client --subnet 172.19.0.0/20
fi
if [ -z $(docker network ls --filter name=^server$ --format="{{ .Name }}") ] ; then
  echo "[STATUS] 'server' network does not exist, setting it up now..."
  docker network create --driver bridge server --subnet 172.18.0.0/20
fi
echo "[STATUS] docker networks are ready."

# Run the sstp-server container and connect the server to both the client and the server network.
if ${WITH_SPLICE}; then
  echo "[STATUS] setting up SSTP server: sstp-server-splice..."
  docker run -d --rm --cpuset-cpus="0,1" --network client --ip="172.19.0.2" --name=sstp-server-splice --privileged sstp-server-splice
  docker network connect --ip="172.18.0.2" server sstp-server-splice
else
  echo "[STATUS] setting up SSTP server: sstp-server..."
  docker run -d --rm --cpuset-cpus="0,1" --network client --ip="172.19.0.2" --name=sstp-server --privileged sstp-server
  docker network connect --ip="172.18.0.2" server sstp-server
fi
echo "[STATUS] SSTP server is ready."

# Wait a little bit until the SSTP server is setup
sleep 5

# Run NUM_CLIENTS SSTP clients and iperf servers
SSTP_CLIENT_IP_BASE=172.19.0.
IPERF_SERVER_IP_BASE=172.18.0.
IP_SUFFIX=3

COUNTER=1
while [ ${COUNTER} -le "${NUM_CLIENTS}" ]
do
  SSTP_CLIENT_IP=${SSTP_CLIENT_IP_BASE}${IP_SUFFIX}
  IPERF_SERVER_IP=${IPERF_SERVER_IP_BASE}${IP_SUFFIX}
  echo "[STATUS] setting up SSTP client: sstp-client-${COUNTER}..."
  docker run -d --rm --cpuset-cpus="2" --privileged --network client --ip=${SSTP_CLIENT_IP} --name=sstp-client-${COUNTER} sstp-client
  echo "[STATUS] setting up iPerf3 server: iperf-server-${COUNTER}..."
  docker run -d --rm --cpuset-cpus="3" --network=server --ip=${IPERF_SERVER_IP} --name=iperf-server-${COUNTER} networkstatic/iperf3 -s
  ((COUNTER++))
  ((IP_SUFFIX++))
done
echo "[STATUS] SSTP clients and iPerf3 servers are ready."

# Wait a little bit until SSTP clients are connected to the SSTP server
sleep 10

# Run NUM_CLIENTS iperf clients
IP_SUFFIX=3
COUNTER=1
while [ ${COUNTER} -le "${NUM_CLIENTS}" ]
do
  IPERF_SERVER_IP=${IPERF_SERVER_IP_BASE}${IP_SUFFIX}
  LOG_NAME=${IPERF_SERVER_IP}-"${NUM_CLIENTS}".log
  if ${WITH_SPLICE}; then
    LOG_NAME=${IPERF_SERVER_IP}-"${NUM_CLIENTS}"-splice.log
  fi
  # Should pin to the same set of CPU as SSTP clients
  # Mount FS so that we can get log data from the host machine
  # Ref: https://docs.docker.com/storage/bind-mounts/
  docker run -d --rm --cpuset-cpus="2" --net=container:sstp-client-${COUNTER} --mount type=bind,source="$(pwd)",target=/var \
  networkstatic/iperf3 -c ${IPERF_SERVER_IP} --logfile /var/"${LOG_NAME}"
  ((COUNTER++))
  ((IP_SUFFIX++))
done
echo "[STATUS] all iPerf3 clients are running, they will be destroyed after they are finished."
echo "[HINT] run clean_up_iperf_experiment.sh to clean up the rest after the experiment is finished."
