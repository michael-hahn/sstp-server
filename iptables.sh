#!/bin/sh

 Ref: https://wiki.archlinux.org/title/PPTP_server
# Ref: https://ppp.samba.org/pppd.html
# Create a sysctl configuration file /etc/sysctl.d/30-ipforward.conf and enable kernel packet forwarding
echo 'net.ipv4.ip_forward=1' > /etc/sysctl.d/30-ipforward.conf
# Apply changes to let the sysctl configuration take effect
sysctl --system
# Accept all packets via ppp* interfaces (for example, ppp0)
iptables -A INPUT -i ppp+ -j ACCEPT
iptables -A OUTPUT -o ppp+ -j ACCEPT
# Enable IP forwarding
iptables -F FORWARD
iptables -A FORWARD -j ACCEPT
# Enable NAT for eth0 on ppp* interfaces
iptables -A POSTROUTING -t nat -o eth0 -j MASQUERADE
iptables -A POSTROUTING -t nat -o ppp+ -j MASQUERADE
