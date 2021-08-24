#!/bin/bash

# This script performs clean up after the entire iperf3 experiment pipeline is finished.

# This script takes a number of flags:
# -s: if set, the SSTP-server is running with SPLICE (default is false)
# -n NUM_CLIENTS: number of SSTP clients (which is the same number of iperf3 clients and iperf3 servers)
# These flags should be set to be the same as the flags set in run_iperf_experiment.sh
# Parse the flags
WITH_SPLICE='false'
while getopts s:u: flag
do
  case "${flag}" in
    s) WITH_SPLICE='true';;
    u) NUM_CLIENTS=${OPTARG};;
    *) echo "UNKNOWN OPTION --> ${OPTKEY}" >&2
       exit 1;;
  esac
done

# Stop the SSTP server
if ${WITH_SPLICE}; then
  echo "[STATUS] stopping SSTP server: sstp-server-splice..."
  docker container stop sstp-server-splice
else
  echo "[STATUS] stopping SSTP server: sstp-server..."
  docker container stop sstp-server
fi
echo "[STATUS] SSTP server is destroyed."

# Stop the SSTP clients and iperf servers
COUNTER=1
while [ ${COUNTER} -le "${NUM_CLIENTS}" ]
do
  echo "[STATUS] stopping iPerf3 server: iperf-server-${COUNTER}..."
  docker container stop iperf-server-${COUNTER}
# Note that once SSTP server is destroyed, SSTP clients are automatically destroyed as well.
# No need to run the following commented commands.
#  echo "[STATUS] stopping SSTP client: sstp-client-${COUNTER}..."
#  docker container stop sstp-client-${COUNTER}
  ((COUNTER++))
done
echo "[STATUS] clean up is finished."
