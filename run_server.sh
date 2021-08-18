#!/bin/sh

# set up the iptables
/usr/local/bin/iptables.sh
# run the sstp-server
python3.8 -O build/lib.linux-x86_64-3.8/sstpd/run.py -f sstp-server-docker.ini -s site1
