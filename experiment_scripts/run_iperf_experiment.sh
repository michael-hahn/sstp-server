#!/bin/bash

# This script runs the iperf3 experiment pipeline, setting up one or more iperf3 servers and one or more iperf3 clients.
# You can find some of the commands used in this script from run_iperf_servers.sh and run_iperf_clients.sh.
# This script assumes that all docker images used in this script have been built successfully (and named correspondingly
# as indicated in this script).

# You should run setup_sstp.sh first before running this script.
# This script does *not* contain code to clean up after the experiment is finished.

# This script takes the following flag(s):
# -s true/false: if set to true, the SSTP server is running with SPLICE (default is false)
# -n NUM_CLIENTS: number of iperf3 clients (which is the same number of SSTP clients and iperf3 servers)
# -u true/false: if set to true, use UDP instead of TCP
# -R RUNTIME: seconds to run the experiment

# Parse the flag(s)
WITH_SPLICE='false'
UDP='false'
while getopts s:n:u:R: flag
do
  case "${flag}" in
    s) WITH_SPLICE=${OPTARG};;
    u) UDP=${OPTARG};;
    n) NUM_CLIENTS=${OPTARG};;
    R) RUNTIME=${OPTARG};;
    *) echo "UNKNOWN OPTION --> ${OPTKEY}" >&2
       exit 1;;
  esac
done

if ${UDP}; then
  echo "[INFO] running iPerf3 UDP experiments with ${NUM_CLIENTS} client connections."
else
  echo "[INFO] running iPerf3 TCP experiments with ${NUM_CLIENTS} client connections."
fi

# Run NUM_CLIENTS iPerf servers
IPERF_SERVER_IP_BASE=172.18.0.
IP_SUFFIX=3

COUNTER=1
while [ ${COUNTER} -le "${NUM_CLIENTS}" ]
do
  IPERF_SERVER_IP=${IPERF_SERVER_IP_BASE}${IP_SUFFIX}
  echo "[STATUS] setting up iPerf3 server: iperf-server-${COUNTER}..."
  docker run -d --rm --cpuset-cpus="3" --network=server --ip=${IPERF_SERVER_IP} --name=iperf-server-${COUNTER} networkstatic/iperf3 -s -J
  ((COUNTER++))
  ((IP_SUFFIX++))
done
echo "[STATUS] ${NUM_CLIENTS} iPerf3 servers are ready."

# Wait a little bit until all iPerf3 servers are set up
sleep 10

# Run NUM_CLIENTS iperf clients
IP_SUFFIX=3
COUNTER=1
while [ ${COUNTER} -le "${NUM_CLIENTS}" ]
do
  IPERF_SERVER_IP=${IPERF_SERVER_IP_BASE}${IP_SUFFIX}
  LOG_NAME=${IPERF_SERVER_IP}-"${NUM_CLIENTS}"
  if ${WITH_SPLICE}; then
    LOG_NAME=${IPERF_SERVER_IP}-"${NUM_CLIENTS}"-splice
  fi
  # Should pin to the same set of CPU as SSTP clients use --cpuset-cpus
  # Mount FS using --mount so that we can get log data from the host machine
  # Ref: https://docs.docker.com/storage/bind-mounts/
  # iPerf3 parameters: (ref: https://www.mankier.com/1/iperf3#)
  # -c: Run iPerf in client mode, connecting to an iPerf server running on ${IPERF_SERVER_IP}
  # -u: Use UDP rather than TCP
  # -b: Set target bitrate to n bits/sec (default 1 Mbit/sec for UDP, unlimited for TCP/SCTP).
  #     Setting the target bitrate to 0 will disable bitrate limits (particularly useful for UDP tests).
  # -t: The time in seconds to transmit data for
  # -O: Omit the first n seconds of the test, to skip past the TCP slowstart period
  # -V: Verbose to give more detailed output
  # --get-server-output: Retrieve the server-side output
  # -J: Output in JSON format for easy parsing of results
  if ${UDP}; then
    docker run -d --rm --cpuset-cpus="2" --net=container:sstp-client-${COUNTER} --mount type=bind,source="$(pwd)",target=/var \
    networkstatic/iperf3 -c ${IPERF_SERVER_IP} -u -b 0 -t "${RUNTIME}" -V --get-server-output -J --logfile /var/"${LOG_NAME}"-udp.json
  else
    docker run -d --rm --cpuset-cpus="2" --net=container:sstp-client-${COUNTER} --mount type=bind,source="$(pwd)",target=/var \
    networkstatic/iperf3 -c ${IPERF_SERVER_IP} -t "${RUNTIME}" -O 2 -V --get-server-output -J --logfile /var/"${LOG_NAME}"-tcp.json
  fi
  ((COUNTER++))
  ((IP_SUFFIX++))
done

# Monitor SSTP server CPU utilization and memory usage and others
if ${WITH_SPLICE}; then
  docker stats --format "table {{.Container}},{{.CPUPerc}},{{.MemPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}}" sstp-server-splice >> cpumem-splice.json &
else
  docker stats --format "table {{.Container}},{{.CPUPerc}},{{.MemPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}}" sstp-server >> cpumem.json &
fi

echo "[STATUS] all iPerf3 clients are running; they will be destroyed after they are finished."
echo "[HINT] do not forget to run clean up scripts to clean up after the experiment is finished."
