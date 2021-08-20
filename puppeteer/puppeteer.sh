#!/bin/bash

# Assume that you have run the server.sh to set up the docker and the repository already
# Assume at this point you just git clone https://github.com/michael-hahn/sstp-server.git

# Ref:
cd ./sstp-server/puppeteer
docker build -t puppeteer .

# Run the container by passing node -e "<yourscript.js content as a string>" as the command:
docker run -i --init --rm --cap-add=SYS_ADMIN --name puppeteer --net=container:sstp-client puppeteer node -e "`cat run.js`"
