#!/bin/bash

# This script cleans up the SSTP infrastructure after an experiment is finished.

# This script takes the following flag(s):
# -s true/false: if set to true, the SSTP server is running with SPLICE (default is false)
# The flag(s) should be set to be the same as the flags set in the experiment.

# Parse the flag(s)
WITH_SPLICE='false'
while getopts s: flag
do
  case "${flag}" in
    s) WITH_SPLICE=${OPTARG};;
    *) echo "UNKNOWN OPTION --> ${OPTKEY}" >&2
       exit 1;;
  esac
done

# Stop the SSTP server
if ${WITH_SPLICE}; then
  echo "[STATUS] stopping SSTP server: sstp-server-splice..."
  docker container stop sstp-server-splice
else
  echo "[STATUS] stopping SSTP server: sstp-server..."
  docker container stop sstp-server
fi
echo "[STATUS] SSTP server is destroyed."

# Note that once SSTP server is destroyed, SSTP clients are automatically destroyed as well.
echo "[STATUS] SSTP clean up is finished."
