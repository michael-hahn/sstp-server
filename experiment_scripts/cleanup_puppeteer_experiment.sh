#!/bin/bash

# This script cleans up the web server after a Puppeteer experiment is finished.

docker container stop web-server

echo "[STATUS] Puppeteer clean up is finished."
