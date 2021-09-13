#!/bin/bash

# Puppeteer experiment
echo "1 2 3 4 5 6" | ./eval_puppeteer_workload.sh -w remote

# TCP experiment
echo "1 2 4 6 8 10" | ./eval_iperf_workload.sh -u false -t 60

# Trial and Error
# echo "3" | ./eval_iperf_workload.sh -u true -t 30
# echo "1" | ./eval_iperf_workload.sh -u false -t 30

