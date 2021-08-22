#!/bin/bash
# RUN MULTIPLE PUPPETEER BROWSERS ON DOCKER
# Check out puppeteer.sh for basic setup first!
# Run run_sstp_clients.sh first to set up SSTP clients.
# Each puppeteer client is attached to an SSTP client.
NUM_CLIENTS=1

counter=1
while [ $counter -le $NUM_CLIENTS ]
do
  # Should pin to the same set of CPU as SSTP clients
  # Mount FS so that we can get log data from the host machine
  # Ref: https://docs.docker.com/storage/bind-mounts/
  docker run -it --init --rm --cpuset-cpus="2" --cap-add=SYS_ADMIN --name puppeteer-${counter} --net=container:sstp-client-${counter} --mount type=bind,source="$(pwd)"/data,target=/home/pptruser/Downloads puppeteer node -e "`cat run.js`"
  ((counter++))
done
