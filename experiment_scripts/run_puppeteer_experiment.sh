#!/bin/bash

# This script runs the puppeteer experiment pipeline, setting up a Web server and one or more web clients (i.e.,
# headless Chrome browsers controlled by Puppeteer). You can find some of the commands used in this script from
# puppeteer.sh and flask.sh. This script assumes that all docker images used in this script have been built successfully
# (and named correspondingly as indicated in this script).

# You should run setup_sstp.sh first before running this script.
# This script does *not* contain code to clean up after the experiment is finished.

# This script takes the following flag(s):
# -n NUM_CLIENTS: number of web clients (which is the same number of SSTP clients)
# -f js file: the name of the Node.js puppeteer file (the file must be in the puppeteer folder)

# Parse the flag(s)
while getopts n:f: flag
do
  case "${flag}" in
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

# Run NUM_CLIENTS web clients in the puppeteer folder
cd ../puppeteer
COUNTER=1
while [ ${COUNTER} -le "${NUM_CLIENTS}" ]
do
  docker run -d --init --rm --cpuset-cpus="2" --cap-add=SYS_ADMIN --name puppeteer-${COUNTER} \
  --net=container:sstp-client-${COUNTER} --mount type=bind,source="$(pwd)"/data,target=/home/pptruser/Downloads \
  puppeteer node -e "$(cat "${PUPPETEER_FILE}")"
  ((COUNTER++))
done

echo "[STATUS] all web clients are running; they will be destroyed after they are finished."
echo "[HINT] do not forget to run clean up scripts to clean up after the experiment is finished."
