#!/bin/sh

# Install Python 3.8 on Ubuntu 18.04
sudo apt-get update
sudo apt-get install python3.8 python3.8-dev python3.8-distutils python3.8-venv python3-wheel -y
# Install Pip
sudo apt-get install python3-pip -y
# Install pppd for the SSTP server
sudo apt-get install ppp-dev ppp -y
# Install Docker from the official Docker repository to get the latest version.
# Ref: https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-18-04
sudo apt-get install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
sudo apt-get update
sudo apt-get install docker-ce -y
# Check to make sure Docker is in fact running now.
sudo systemctl status docker
# Avoid typing sudo whenever you run the docker command.
sudo usermod -aG docker ${USER}
# To apply the new group membership, log out of the server and back in.
# You will be prompted to enter your user’s password to continue.
su - ${USER}
# Check to confirm that user is now added to the docker group.
id -nG

# Set up git to cache username and password: you will still need to provide username and password once!
git config --global credential.helper store
# Repository needed to run the server
git clone https://github.com/michael-hahn/sstp-server.git
cd ./sstp-server
# ======= WE WILL USE DOCKER INSTEAD OF SETTING SSTP SERVER ON HOST ==========================
## We need to run setup.py because it builds the C extension module.
#sudo python3.8 setup.py install
## We provide options file to pppd.
#sudo cp options.sstpd /etc/ppp/
## We modify Python's asyncio for taint tracking, so we will replace the original code.
#sudo cp asyncio/sslproto.py /usr/lib/python3.8/asyncio/sslproto.py
#sudo cp asyncio/unix_events.py /usr/lib/python3.8/asyncio/unix_events.py
## FIXME: Temporarily we move a splice folder in the sstp-server repository to Python's asyncio
## FIXME: folder. Later, Splice should be a standalone package from a separate repository!
#sudo cp -r splice/ /usr/lib/python3.8/asyncio/
## After build we can now run run.py in the build/lib.linux-x86_64-3.8/sstpd folder.
## Note that on a different platform, 'lib.linux-x86_64-3.8' might be called differently.
#cd build/lib.linux-x86_64-3.8/sstpd
#sudo python3.8 -O run.py -f ~/sstp-server/sstp-server.ini -s site1
# ============================================================================================
# Ref: https://docs.docker.com/network/network-tutorial-standalone/#use-user-defined-bridge-networks
# Create the 'client' and the 'server' network. You do not need the --driver bridge flag since it’s the default,
# but this example shows how to specify it.
docker network create --driver bridge client --subnet 172.19.0.0/20
docker network create --driver bridge server --subnet 172.18.0.0/20
# List Docker’s networks
docker network ls
# Inspect the 'client' network. This shows you its IP address and the fact that no containers are connected to it
docker network inspect client
# Build the docker image for SSTP server
docker build --tag sstp-server .

# Ideally run the following in a separate console (e.g., using tmux)
# Run the sstp-server container
# Use CPU affinity to bind the docker container to a given CPU or CPUs
# Ref: https://docs.docker.com/engine/reference/run/#runtime-constraints-on-resources
# We use our user-defined bridged network called client to place SSTP-server on a fixed IP
docker run --cpuset-cpus="0,1" --network client --ip="172.19.0.2" --name=sstp-server --privileged sstp-server
# Also connect the server to the server network.
# Note that you can only connect to one network during the docker run command, so you need to use docker network
# connect afterward to connect sstp-server to the 'client' network as well.
docker network connect --ip="172.18.0.2" server sstp-server
# Now you can explore the sstp-server container with a shell (bash) session of this container
# such as running commands like
# /# netstat -rn
# /# iptables -S
# Ref: https://geekflare.com/check-docker-network-connections/
docker exec -it sstp-server bash

# iperf3 experiments for stress testing
# Ideally run the following in a separate console (e.g., using tmux)
# Run an iperf3 server on the server network using iperf docker
# Ref: https://hub.docker.com/r/networkstatic/iperf3/
docker run -it --rm --name=iperf3-server --network=server networkstatic/iperf3 -s

# Ideally run the following in a separate console (e.g., using tmux)
# Run an Apache HTTPd server on the server network
# Ref: https://hub.docker.com/r/jordi/ab
docker run -d --name=httpd --network server jordi/server:http

# BUILD SSTP CLIENT IN CLIENTS FOLDER NOW!!!

# MORE USEFUL LINKS ====================================================================================================
# Docker networking tutorial
# https://docs.docker.com/network/network-tutorial-standalone/#use-user-defined-bridge-networks
# Useful tcpdump commands:
# https://danielmiessler.com/study/tcpdump/
# How to add/delete a route from a routing table
# https://www.linuxtechi.com/add-delete-static-route-linux-ip-command/
# https://serverfault.com/questions/181094/how-do-i-delete-a-route-from-linux-routing-table
# Set up iptable rules automatically in a container
# https://serverfault.com/questions/977904/automatic-iptables-rules-inside-docker-container

# NOTES ================================================================================================================
# # Ref: https://wiki.archlinux.org/title/PPTP_server
# # Ref: https://ppp.samba.org/pppd.html
# # Create a sysctl configuration file /etc/sysctl.d/30-ipforward.conf and enable kernel packet forwarding
# echo 'net.ipv4.ip_forward=1' > /etc/sysctl.d/30-ipforward.conf
# # Apply changes to let the sysctl configuration take effect
# sysctl --system
# # Accept all packets via ppp* interfaces (for example, ppp0)
# iptables -A INPUT -i ppp+ -j ACCEPT
# iptables -A OUTPUT -o ppp+ -j ACCEPT
# # Enable IP forwarding
# iptables -F FORWARD
# iptables -A FORWARD -j ACCEPT
# # Enable NAT for eth0 on ppp* interfaces
# iptables -A POSTROUTING -t nat -o eth0 -j MASQUERADE
# iptables -A POSTROUTING -t nat -o ppp+ -j MASQUERADE
# # Save the new iptables rules
# iptables-save > /etc/iptables/iptables.rules
# systemctl enable iptables.service

# # Configure ufw settings to enable access for SSTP Clients.
# # In /etc/default/ufw, change to:
# DEFAULT_FORWARD_POLICY="ACCEPT"
# # Change /etc/ufw/before.rules, add following code after header and before *filter line
# # nat Table rules
# *nat
# :POSTROUTING ACCEPT [0:0]

# # Allow traffic from clients to eth0
# -A POSTROUTING -s 192.168.1.0/24 -o eth0 -j MASQUERADE
# -A POSTROUTING -s 10.0.0.240 -o eth0 -j MASQUERADE

# # commit to apply changes
# COMMIT

# In fact, let us just disable ufw for now
# ufw disable


# # Other useful commands for the client-side
# # macOS:
# # Add a new entry to the routing table so that the destination address
# # (in this example, 10.0.0.241) go through a specific interface (again
# # in the example, ppp0)
# sudo route add -host 10.0.0.241 -interface ppp0
# # Get some information about the routing table
# netstat -rn
# # Trace through the route to a specific address (in the example 10.0.0.241)
# traceroute 10.0.0.241

# # Run iperf3 as a client to communicate with the IP address that runs
# # the iperf3 server (in this example, 10.0.0.241 should run iperf3 in server mode).
# ./iperf3 -c 10.0.0.241
# # Note that iperf3 has a bind option -B for the client as well (just like AB below).
# # Therefore, you can do something like:
# ./iperf3 -c 10.0.0.241 -B 192.168.20.2 --cport 8080
# # Where the IP address is the one associated with ppp.
# # Note that for some reason, the connection can be slow using the -B and --cport approach
# # If so, try to bind through iptable before running iperf3 (so no need to use -B and --cport).
# # Note also that you must specify -B if you specify --cport, but you don't need to
# # specify --cport if you specify -B.

# # Apache Benchmark (ab):
# # No need to bind the interface through iptable.
# # At the client side run:
# ab -n 100 -c 1 -B 192.168.20.2 https://10.0.0.241/
# # Where -B does the binding automatically.
# # Make sure the server runs Apache server with SSL. Ref:
# # https://ubiq.co/tech-blog/how-to-create-a-self-signed-ssl-certificate-for-apache-in-ubuntu-debian/
# # Check server side status:
# systemctl status apache2

# # Connect to your VPN and execute the command in terminal:
# ifconfig | grep inet | grep mask
# # You should see the output similar to:
# mvanbastelaer@Michaels-MacBook-Pro sstp-server % ifconfig | grep inet | grep mask
#         inet 127.0.0.1 netmask 0xff000000
#         inet 10.0.0.32 netmask 0xffffff00 broadcast 10.0.0.255
#         inet 192.168.33.1 netmask 0xffffff00 broadcast 192.168.33.255
#         inet 192.168.20.2 --> 192.168.20.1 netmask 0xffffff00
# # The First line is the localhost, second is the local IP in LAN, third is the docker network and the last is the VPN.
# # To check your docker networks, you can use this command:
# docker network inspect `docker network ls -q` | grep Subnet
# # It returns something like:
# mvanbastelaer@Michaels-MacBook-Pro docker % docker network inspect `docker network ls -q` | grep Subnet
#                     "Subnet": "172.17.0.0/16",

# # See all traffic on port 443:
# sudo tcpdump -ni any port 443

# # Networking features in Docker Desktop for Mac:
# # https://docs.docker.com/docker-for-mac/networking/