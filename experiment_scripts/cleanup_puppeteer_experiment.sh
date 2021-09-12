#!/bin/bash

# This script cleans up the web server after a Puppeteer experiment is finished.

# This script takes the following flag(s):
# -s true/false: if set to true, the SSTP server is running with SPLICE (default is false)
# -n NUM_CLIENTS: number of puppeteer clients
# -f remote/local: data from either a local server or a remote server
# The flag(s) should be set to be the same as the flags set in the experiment.

# Parse the flag(s)
WITH_SPLICE='false'
while getopts s:n:f: flag
do
  case "${flag}" in
    s) WITH_SPLICE=${OPTARG};;
    n) NUM_CLIENTS=${OPTARG};;
    f) SERVER=${OPTARG};;
    *) echo "UNKNOWN OPTION --> ${OPTKEY}" >&2
       exit 1;;
  esac
done

# Stop docker stats process
pid=$(ps aux | grep "docker stats" | grep -v grep | awk '{print $2}')
kill -9 "${pid}"

docker container stop web-server

# Stop the puppeteer containers just in case (it's OK if the command fails when the container has already been stopped)
for (( i=1; i<=${NUM_CLIENTS}; i++ ))
do
  docker container stop puppeteer-"${i}"
done

echo "[STATUS] Puppeteer clean up is finished."

mkdir -p data/
cd data/
NEW_FOLDER=puppeteer-${NUM_CLIENTS}
if [ "${SERVER}" = "local" ]; then
  NEW_FOLDER+="-local"
else
  NEW_FOLDER+="-remote"
fi
if [ "${WITH_SPLICE}" = "true" ]; then
  NEW_FOLDER+="-splice"
fi
mkdir ${NEW_FOLDER}
cd ..
mv ../puppeteer/data/*.json data/${NEW_FOLDER}
mv ../puppeteer/data/*.log data/${NEW_FOLDER}
# mv ../puppeteer/data/*.png data/${NEW_FOLDER}

echo "[STATUS] all experimental data is moved to data/${NEW_FOLDER}"
