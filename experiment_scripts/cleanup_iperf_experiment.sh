#!/bin/bash

# This script cleans up iPerf3 servers after an iPerf3 experiment is finished.

# This script takes the following flag(s):
# -s true/false: if set to true, the SSTP server is running with SPLICE (default is false)
# -u true/false: if set to true, use UDP instead of TCP
# -n NUM_CLIENTS: number of iPerf3 servers
# The flag(s) should be set to be the same as the flags set in the experiment.

# Parse the flag(s)
WITH_SPLICE='false'
UDP='false'
while getopts s:u:n: flag
do
  case "${flag}" in
    s) WITH_SPLICE=${OPTARG};;
    u) UDP=${OPTARG};;
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

mkdir -p data/
cd data/
NEW_FOLDER=iperf-${NUM_CLIENTS}
if [ "${UDP}" = "true" ]; then
  NEW_FOLDER+="-udp"
else
  NEW_FOLDER+="-tcp"
fi
if [ "${WITH_SPLICE}" = "true" ]; then
  NEW_FOLDER+="-splice"
fi
mkdir ${NEW_FOLDER}
mv *.json ${NEW_FOLDER}

echo "[STATUS] all experimental data is moved to data/${NEW_FOLDER}"