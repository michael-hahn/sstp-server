#!/bin/bash

# This script sets up the docker networks (if not set already) and the SSTP server for deletion workload.
# You can find some of the commands used in this script from server.sh and run_sstp_clients.sh (in clients/).
# This script assumes that all docker images used in this script have been built successfully (and named correspondingly
# as indicated in this script).

# You should always run this script first before running experiments.

# This script takes no flags.

echo "[INFO] SPLICE DELETION WORKLOAD."

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

# Run the SSTP server container and connect the server to both the client network.
# We need to connect the server to the server network in a different console window.
# Add sys_ptrace for profiling purposes only. The server performance is limited by the main SSTP process.
echo "[STATUS] setting up SSTP server: sstp-server-splice..."
docker run -it --rm --cpuset-cpus="0,1" --network client --ip="172.19.0.2" --cap-add sys_ptrace --name=sstp-server-del --privileged sstp-server-del

# We will keep the server running in the foreground.
# The rest of the experiment should be done in a different console window.

