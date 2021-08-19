#!/bin/bash

sstpc --log-level 3 --log-stderr --cert-warn --user user --password password 172.19.0.2:443 usepeerdns require-pap noipdefault nodefaultroute &
sleep 5
route add default gw 192.168.20.1 ppp0
wait
