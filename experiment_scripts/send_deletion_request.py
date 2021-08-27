# This python script simulates a client sends a Splice deletion request to the SSTP server,
# so that we do not need to modify the sstpc client application. To delete a specific client,
# we need to know its unique taint value (this will be printed out in the server console
# when a client is connected to the server). Use this taint value (which should be an int) as
# the argument to run this script for Splice deletion.

# We assume the SSTP server is at 172.19.0.2. We also assume the existence of cert.pem in the
# parent directory (note that SSL is a must to run this client properly). However, these are
# arguments to this script that can be changed if needed.

import socket
import ssl
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-H', '--host', help='SSTP server IP', default='172.19.0.2')
parser.add_argument('-p', '--port', help='SSTP server port', type=int, default=443)
parser.add_argument('-c', '--certs', help='path to certificate', default='../cert.pem')
parser.add_argument('-t', '--taint', help='taint ID of the user to be deleted', type=int, required=True)
args = parser.parse_args()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    with ssl.wrap_socket(s, cert_reqs=ssl.CERT_REQUIRED, ca_certs=args.certs) as ssock:
        ssock.connect((args.host, args.port))
        # Send a simple SPLICE deletion request with taint
        ssock.sendall(bytes('SPLICE:{}'.format(args.taint), 'utf8'))
        data = ssock.recv(1024)
print('Response from the SSTP server:{}'.format(data))
