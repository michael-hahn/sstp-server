#!/bin/bash

# Assume that you have run the server.sh to set up the docker and the repository already
# Assume at this point you just git clone https://github.com/michael-hahn/sstp-server.git

cd ./sstp-server/flask
# Build the docker image for flask server
docker build -t flask .

# Ideally run the following in a separate console (e.g., using tmux)
# Run the flask container
docker run -it --name=flask --network=server --ip="172.18.0.5" flask
