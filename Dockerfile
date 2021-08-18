# syntax=docker/dockerfile:1
# set base image (host OS)
FROM ubuntu:18.04
# set the working directory in the container
WORKDIR /server

RUN apt-get update
RUN apt-get install python3.8 python3.8-dev python3.8-distutils python3.8-venv python3-wheel -y
RUN apt-get install python3-pip -y
RUN apt-get install ppp-dev ppp -y
RUN apt-get install iptables -y

# copy the dependencies file to the working directory
COPY cert.pem cert.pem
COPY key.pem key.pem
COPY options.sstpd options.sstpd
COPY chap-secrets chap-secrets
COPY pap-secrets pap-secrets
COPY setup.py setup.py
COPY sstp-server-docker.ini sstp-server-docker.ini
COPY README.rst README.rst
COPY iptables.sh /usr/local/bin/iptables.sh
COPY run_server.sh run_server.sh
COPY asyncio/ asyncio/
COPY splice/ splice/
COPY sstpd/ sstpd/

# to be able to run iptable.sh and run.sh
RUN chmod +x /usr/local/bin/iptables.sh
RUN chmod +x run_server.sh
# install
RUN python3.8 setup.py install

RUN cp options.sstpd /etc/ppp/
RUN cp chap-secrets /etc/ppp/
RUN cp pap-secrets /etc/ppp/
RUN cp asyncio/sslproto.py /usr/lib/python3.8/asyncio/sslproto.py
RUN cp asyncio/unix_events.py /usr/lib/python3.8/asyncio/unix_events.py
RUN cp -r splice/ /usr/lib/python3.8/asyncio/
# Need /dev/ppp module to run ppp
RUN mknod /dev/ppp c 108 0

# CMD ["python3.8", "-O", "build/lib.linux-x86_64-3.8/sstpd/run.py", "-f", "sstp-server-docker.ini", "-s", "site1"]
# We run to run iptable.sh and the command above, so we run it in a separate shell script.
CMD ./run_server.sh
