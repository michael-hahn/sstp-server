#!/bin/bash

# This script runs the puppeteer experiment pipeline, setting up a Web server and one or more web clients (i.e.,
# headless Chrome browsers controlled by Puppeteer). You can find some of the commands used in this script from
# puppeteer.sh and flask.sh. This script assumes that all docker images used in this script have been built successfully
# (and named correspondingly as indicated in this script).

# You should run setup_sstp.sh first before running this script.
# This script does *not* contain code to clean up after the experiment is finished.

# This script takes the following flag(s):
# -s true/false: if set, the SSTP server is running with SPLICE (default is false)
# -n NUM_CLIENTS: number of web clients (which is the same number of SSTP clients)
# -f js file: the name of the Node.js puppeteer file (the file must be in the puppeteer folder)

# Parse the flag(s)
while getopts s:n:f: flag
do
  case "${flag}" in
    s) WITH_SPLICE=${OPTARG};;
    n) NUM_CLIENTS=${OPTARG};;
    f) PUPPETEER_FILE=${OPTARG};;
    *) echo "UNKNOWN OPTION --> ${OPTKEY}" >&2
       exit 1;;
  esac
done

# Run the web server container
echo "[STATUS] setting up the web server: web-server..."
docker run -d --rm --name=web-server --network=server --ip="172.18.0.5" flask
echo "[STATUS] the web server is ready."

# Wait a little bit until the web server is set up
sleep 5

# Run the rest of the code in the puppeteer folder
cd ../puppeteer

# Get the pid of the server process (to monitor its CPU and memory usage)
pid=$(ps aux | grep "run.py" | grep -v grep | awk '{print $2}')
# Monitor using top every second and parse the comma-separated output with awk (pin to core 4)
# The format is: TIME,PID,VIRT,RES,%CPU,%MEM
taskset 0x10 top -b -n 60 -d 1 -p "${pid}" | awk -v OFS=',' '$1=="top" { time=$3 } $1+0>0 { print time,$1,$5,$6,$9,$10; fflush(); }' >> data/"${NUM_CLIENTS}"_server-cpumem.log &

# Run NUM_CLIENTS web clients
COUNTER=1
CPU1=4
CPU2=5
while [ ${COUNTER} -le "${NUM_CLIENTS}" ]
do
  # Change the log file path (by replacement using sed) so that each puppeteer process will write to a separate log file
  path_line="const logpath = dir.concat(${COUNTER}, '.json');"
  sed -i "17s;.*;${path_line};" "${PUPPETEER_FILE}"

  docker run -d --init --rm --cpuset-cpus="${CPU1},${CPU2}" --cap-add=SYS_ADMIN --name puppeteer-${COUNTER} \
  --net=container:sstp-client-${COUNTER} --mount type=bind,source="$(pwd)"/data,target=/home/pptruser/Downloads \
  puppeteer node -e "$(cat "${PUPPETEER_FILE}")"
  ((COUNTER++))
  CPU1=$(( "${CPU1}" + 2 ))
  CPU2=$(( "${CPU2}" + 2 ))
done

# Monitor SSTP server and Puppeteer clients CPU utilization and memory usage and others
# TODO: For some reason, cannot specify puppeteer containers through string concatenation to stats; just capture all running containers for now
if ${WITH_SPLICE}; then
  docker stats --format "table {{.Name}},{{.CPUPerc}},{{.MemPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}}" >> data/cpumem-splice.log &
else
  docker stats --format "table {{.Name}},{{.CPUPerc}},{{.MemPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}}" >> data/cpumem.log &
fi

echo "[STATUS] all web clients are running; they will be destroyed after they are finished."
echo "[HINT] do not forget to run clean up scripts to clean up after the experiment is finished."

# Check if any puppeteer container is running every second and finishes running if and only if all puppeteer containers are done
COUNTER=1
while [ ${COUNTER} -le "${NUM_CLIENTS}" ]
do
  while [ "$( docker container inspect -f '{{.State.Running}}' puppeteer-${COUNTER} )" == "true" ]
  do
    echo "[STATUS] waiting for puppeteer-${COUNTER} to finish..."
    sleep 1
  done
  ((COUNTER++))
done

