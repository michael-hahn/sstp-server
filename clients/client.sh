#!/bin/bash

# Assume that you have run the server.sh to set up the docker and the repository already
# Assume at this point you just git clone https://github.com/michael-hahn/sstp-server.git

cd ./sstp-server/clients
# Build the docker image for SSTP client
docker build --tag sstp-client .
# Ideally run the following in a separate console (e.g., using tmux)
# Run the sstp-client container (pin to CPU 2)
docker run --cpuset-cpus="2" --privileged --network client --ip="172.19.0.3" --name=sstp-client sstp-client

# Now you can explore the sstp-client container with a shell (bash) session of this container
docker exec -it sstp-client bash

# iperf client
# Get the IP address of the iperf server container
docker inspect iperf3-server
# --net: the iperf client uses sstp-client's network
# -c: the IP address of the iperf server container
# [OPTIONAL] The following arguments should not be needed since we set up the IP table correctly
# -B: bind to the IP address of ppp0 on the sstp-client
# --cport: the client port
docker run -it --rm --net=container:sstp-client networkstatic/iperf3 -c 172.18.0.4 # -B 192.168.20.2 --cport 8080

# Ideally run the following in a separate console (e.g., using tmux)
# Get the IP address of the server by inspecting the container
docker inspect httpd
# Run Apache Benchmark (as a client) using Docker
docker run --rm --net=container:sstp-client jordi/ab -k -c 1 -n 100 172.18.0.3
