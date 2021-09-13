#!/bin/bash
# This is the main script that runs the puppeteer workload.
# It takes the following arguments
# -w WORKLOAD: choose from 'local' or 'remote'
# When it runs, it will prompt the user to specify the number of clients to run.

while getopts w: flag
do
  case "${flag}" in
    w) WORKLOAD=${OPTARG};;
    *) echo "Unknown option: ${OPTKEY}" >&2 ; exit 1;;
  esac
done

read -p "Enter a list of numbers of SSTP clients to run the puppeteer ${WORKLOAD} workload, separated by space: " input

# shellcheck disable=SC2068
for NUM_CLIENTS in ${input[@]}
do
  ./setup_sstp.sh -s true -n "${NUM_CLIENTS}"
  ./run_puppeteer_experiment.sh -s true -n "${NUM_CLIENTS}" -f ../puppeteer/run_"${WORKLOAD}".js
  ./cleanup_puppeteer_experiment.sh -s true -n "${NUM_CLIENTS}" -f "${WORKLOAD}"
  ./cleanup_sstp.sh -s true

  ./setup_sstp.sh -s false -n "${NUM_CLIENTS}"
  ./run_puppeteer_experiment.sh -s false -n "${NUM_CLIENTS}" -f ../puppeteer/run_"${WORKLOAD}".js
  ./cleanup_puppeteer_experiment.sh -s false -n "${NUM_CLIENTS}" -f "${WORKLOAD}"
  ./cleanup_sstp.sh -s false
  
done

