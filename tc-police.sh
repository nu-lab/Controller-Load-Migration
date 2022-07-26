#!/bin/bash

#=================
IFACE=$1

RATE=$2
BURST=$3
DELAY=$4
LIMIT=$5
# tc qdisc add dev $IFACE root handle 1:0 tbf mpu 512 rate 1030kbps limit 100k burst 1k delay


tc qdisc replace dev $IFACE handle 1: root htb default 11
# tc filter add dev $IFACE protocol ip parent 1: prio 1 u32 match ip dport 4445 0xffff flowid 1:4
# tc qdisc add dev $IFACE parent 1:4 handle 40: netem delay 5ms
 
tc class add dev $IFACE parent 1: classid 1:1 htb rate $RATE burst $BURST
tc class add dev $IFACE parent 1:1 classid 1:11 htb rate $RATE burst $BURST
tc qdisc add dev $IFACE parent 1:11 handle 10: netem delay $DELAY limit $LIMIT


# tc class add dev $IFACE parent 1: classid 1:1 tbf mpu 500 rate 100kbps limit 10k burst 10k
# tc class add dev $IFACE parent 1:1 classid 1:10 tbf mpu 500 rate 100kbps limit 10k burst 10k

# tc qdisc add dev $IFACE parent 1:10 handle 20: pfifo limit 2

#=================
# IFACE=$1

# tc qdisc add dev $IFACE handle ffff: ingress
# tc filter add dev $IFACE parent ffff: u32 match u32 0 0 police rate 200kbit burst 5k drop

#=================
# ovs-vsctl set interface $IFACE ingress_policing_rate=1000
# ovs-vsctl set interface $IFACE ingress_policing_burst=150
