#!/bin/bash

# This script sets up the docker networks (if not set already), the SSTP server, and one or more SSTP clients.
# You can find some of the commands used in this script from server.sh and run_sstp_clients.sh (in clients/).
# This script assumes that all docker images used in this script have been built successfully (and named correspondingly
# as indicated in this script).

# You should always run this script first before running experiments.

# This script takes the following flag(s):
# -s true/false: if set, the SSTP server is running with SPLICE (default is false)
# -n NUM_CLIENTS: number of SSTP clients

# Parse the flag(s)
WITH_SPLICE='false'
while getopts s:n: flag
do
  case "${flag}" in
    s) WITH_SPLICE=${OPTARG};;
    n) NUM_CLIENTS=${OPTARG};;
    *) echo "UNKNOWN OPTION --> ${OPTKEY}" >&2
       exit 1;;
  esac
done

echo "[INFO] SPLICE is enabled: ${WITH_SPLICE}."

# Create the 'client' and the 'server' network. You do not need the --driver bridge flag since it’s the default,
# but this script shows how to specify it.
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

# Run the SSTP server container and connect the server to both the client and the server network.
# Add sys_ptrace for profiling purposes only. The server performance is limited by the main SSTP process.
if ${WITH_SPLICE}; then
  echo "[STATUS] setting up SSTP server: sstp-server-splice..."
  docker run -d --rm --cpuset-cpus="0,1" --network client --ip="172.19.0.2" --cap-add sys_ptrace --name=sstp-server-splice --privileged sstp-server-splice
  docker network connect --ip="172.18.0.2" server sstp-server-splice
else
  echo "[STATUS] setting up SSTP server: sstp-server..."
  docker run -d --rm --cpuset-cpus="0,1" --network client --ip="172.19.0.2" --cap-add sys_ptrace --name=sstp-server --privileged sstp-server
  docker network connect --ip="172.18.0.2" server sstp-server
fi
echo "[STATUS] SSTP server is ready."

# Wait a little bit until the SSTP server is set up
sleep 5

# Run NUM_CLIENTS SSTP clients
SSTP_CLIENT_IP_BASE=172.19.0.
IP_SUFFIX=3

COUNTER=1
while [ ${COUNTER} -le "${NUM_CLIENTS}" ]
do
  SSTP_CLIENT_IP=${SSTP_CLIENT_IP_BASE}${IP_SUFFIX}
  echo "[STATUS] setting up SSTP client: sstp-client-${COUNTER}..."
  docker run -d --rm --cpuset-cpus="2,3" --privileged --network client --ip=${SSTP_CLIENT_IP} --name=sstp-client-${COUNTER} sstp-client
  ((COUNTER++))
  ((IP_SUFFIX++))
done
echo "[STATUS] ${NUM_CLIENTS} SSTP clients are ready."

# Wait a little bit until SSTP clients are connected to the SSTP server
sleep 10

echo "[STATUS] all SSTP clients are running."
echo "[HINT] you can now run other experiment scripts."
