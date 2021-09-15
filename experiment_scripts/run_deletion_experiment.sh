#!/bin/bash

# This script should run *after* setup_sstp_del.sh is running.

# This script takes the following flag(s):
# -n NUM_CLIENTS: number of SSTP clients

# Parse the flag(s)
UDP='false'
while getopts n: flag
do
  case "${flag}" in
    n) NUM_CLIENTS=${OPTARG};;
    *) echo "UNKNOWN OPTION --> ${OPTKEY}" >&2
       exit 1;;
  esac
done

# Connect the server to the server network first. 
docker network connect --ip="172.18.0.2" server sstp-server-del

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

