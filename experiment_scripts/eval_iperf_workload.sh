#!/bin/bash
# This is the main script that runs the iPerf workload.
# It takes the following arguments
# -u true/false: if set, we run UDP instead of TCP
# -t RUNTIME: time to run the workload
# When it runs, it will prompt the user to specify the number of clients to run.

while getopts u:t: flag
do
  case "${flag}" in
    u) UDP=${OPTARG};;
    t) RUNTIME=${OPTARG};;
    *) echo "Unknown option: ${OPTKEY}" >&2 ; exit 1;;
  esac
done

read -p "Enter a list of numbers of SSTP clients to run the iPerf workload, separated by space: " input

# shellcheck disable=SC2068
for NUM_CLIENTS in ${input[@]}
do
  # Set up the SSTP server and SSTP client daemons
  ./setup_sstp.sh -s false -n "${NUM_CLIENTS}"
  ./run_iperf_experiment.sh -s false -u "${UDP}" -n "${NUM_CLIENTS}" -R "${RUNTIME}"
  ./cleanup_iperf_experiment.sh -s false -u "${UDP}" -n "${NUM_CLIENTS}"
  ./cleanup_sstp.sh -s false

  ./setup_sstp.sh -s true -n "${NUM_CLIENTS}"
  ./run_iperf_experiment.sh -s true -u "${UDP}" -n "${NUM_CLIENTS}" -R "${RUNTIME}"
  ./cleanup_iperf_experiment.sh -s true -u "${UDP}" -n "${NUM_CLIENTS}"
  ./cleanup_sstp.sh -s true
done

