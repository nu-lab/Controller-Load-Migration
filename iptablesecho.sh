#!/bin/bash
exec &> ./logs/echo-$2-$3.log

ifconfig; 

IFACE=$1
MYIP=$2
SIP=$3;
#enable forwarding on our interface
sysctl net.ipv4.conf.$IFACE.forwarding=1

echo redirect $MYIP to $SIP; 
iptables -w 5 -t nat -A PREROUTING -p udp -i $IFACE -s $SIP -j DNAT --to-destination $SIP
echo prerouting passed
iptables -w 5 -t nat -A POSTROUTING -p udp -d $SIP -j SNAT --to $MYIP
echo postrouting passed
# forward the DNATted and SNATtted packet
iptables -w 5 -A FORWARD -p udp -s $MYIP -j ACCEPT
echo forward passed