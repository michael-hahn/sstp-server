# syntax=docker/dockerfile:1
# set base image (host OS)
FROM ubuntu:18.04
# set the working directory in the container
WORKDIR /client

RUN apt-get update
RUN apt-get install ppp-dev ppp -y
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:eivnaes/network-manager-sstp -y
RUN apt-get update
RUN apt-get install network-manager-sstp sstp-client -y
RUN apt-get install net-tools -y

COPY chap-secrets chap-secrets
COPY pap-secrets pap-secrets
COPY options options
COPY run_client.sh run_client.sh
RUN chmod +x run_client.sh
RUN cp options /etc/ppp/
RUN cp chap-secrets /etc/ppp/
RUN cp pap-secrets /etc/ppp/
RUN mknod /dev/ppp c 108 0

# CMD ["sstpc", "--log-level", "3", "--log-stderr", "--cert-warn", "--user", "user", "--password", "password", "172.19.0.2:443", "usepeerdns", "require-pap", "noipdefault", "nodefaultroute"]
CMD ./run_client.sh
