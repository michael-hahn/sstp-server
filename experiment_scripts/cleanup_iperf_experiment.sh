#!/bin/bash

# This script cleans up iPerf3 servers after an iPerf3 experiment is finished.

# This script takes the following flag(s):
# -n NUM_CLIENTS: number of iPerf3 servers
# The flag(s) should be set to be the same as the flags set in the experiment.

# Parse the flag(s)
while getopts n: flag
do
  case "${flag}" in
    n) NUM_CLIENTS=${OPTARG};;
    *) echo "UNKNOWN OPTION --> ${OPTKEY}" >&2
       exit 1;;
  esac
done

# Stop the running iPerf servers
COUNTER=1
while [ ${COUNTER} -le "${NUM_CLIENTS}" ]
do
  echo "[STATUS] stopping iPerf3 server: iperf-server-${COUNTER}..."
  docker container stop iperf-server-${COUNTER}
  ((COUNTER++))
done

echo "[STATUS] iPerf3 clean up is finished."
