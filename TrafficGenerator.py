import os
import sys
import time
import datetime
import subprocess
import pickle
import socket
import multiprocessing
import string
import itertools
import psutil
import timeit
import functools
import random
import math 
import traceback
import numpy as np

from mininet.net import Mininet
import constants as cons


class TrafficGenerator:
    def __init__(self, net, config):

        self.config = config

        src_ctrlr = net.get("h4") 
        dst_ctrlr = net.get("h5") 
        mig_switch = net.get("h3") 
        
        self.flows = [
            {"src": mig_switch, "dst": dst_ctrlr, "base_port": 4445,    
             "n_conn": 1,  "n_packets": cons.BASE_PACKET_RATE },

            {"src": mig_switch, "dst": src_ctrlr, "base_port": 4444,    
             "n_conn": 1,  "n_packets": cons.BASE_PACKET_RATE },
            
            {"src": net.get("h1"), "dst": src_ctrlr, "base_port": 33333,   
             "n_conn": (int) (config["csrc_load"] * config["n1"]), 
             "n_packets": cons.BASE_PACKET_RATE},

            {"src":  net.get("h2"), "dst": dst_ctrlr, "base_port": 44444,   
             "n_conn": (int) (config["cdst_load"] * config["n2"]), 
             "n_packets": cons.BASE_PACKET_RATE},
        ]

        self.src_ctrlr = src_ctrlr
        self.dst_ctrlr = dst_ctrlr

    def start(self):
        self.start_servers()
        self.start_senders()

    def start_servers(self):
        for host in [self.src_ctrlr, self.dst_ctrlr]:
            command = "taskset -c {} ITGRecv -q 1000 -l {}/{}.out < /dev/null &".format(
                cons.CORES['ITGRecv'][host.name][0],
                cons.TRAFFIC_RECV_LOGS_DIR,
                host.name) 
            host.cmd(command)

        # self.src_ctrlr.popen("./iptablesecho.sh h4-eth0 10.0.0.4 10.0.0.3")
        # self.src_ctrlr.popen("./iptablesecho.sh h4-eth0 10.0.0.4 10.0.0.1")
        # self.dst_ctrlr.popen("./iptablesecho.sh h5-eth0 10.0.0.5 10.0.0.3")
        # self.dst_ctrlr.popen("./iptablesecho.sh h5-eth0 10.0.0.5 10.0.0.2")
        

    def start_senders(self): 
        duration = cons.ITG_SEND_TIME
        batch_size = cons.ITG_BATCH_SIZE  

        for flow in self.flows: 
            src = flow['src']
            dst = flow['dst']
            n_conn = flow['n_conn']
            base_port = flow["base_port"]
            n_packets = flow["n_packets"]
            

            n_batches = int(math.ceil(float(n_conn)/batch_size))
            remaining = n_conn     
            for j in range(1,n_batches+1):
                script_file = "{}/{}-{}-{}.script".format(cons.TRAFFIC_SEND_SCRIPT_DIR,src.name, dst.name, j)

                with open(script_file, 'w') as f:
                    count = batch_size if remaining > batch_size else remaining
                    for i in range(count):
                        flow_cmd = "-a {} -T TCP -D -rp {} -c {} -{} {} -t {} -d {}\n".format(
                                        dst.IP(),
                                        base_port + (j-1) * batch_size + i,
                                        cons.PACKET_SIZE,
                                        self.config['interdept'],
                                        n_packets,
                                        duration,
                                        2) #random.randint(0,9))
                        f.write(flow_cmd)
                    remaining -= batch_size
            time.sleep(0.2)

            core_counter = 0
            available_cores = cons.CORES['ITGSend'][src.name]

            for j in range(1,n_batches+1):
                script_file = "{}/{}-{}-{}.script".format(cons.TRAFFIC_SEND_SCRIPT_DIR, src.name, dst.name, j)
                log_address = "{}/{}-{}-{}.log".format(cons.TRAFFIC_SEND_LOGS_DIR, src.name, dst.name, j)
                command = "taskset -c {} ITGSend {} -l {} < /dev/null &".format(
                                        str(available_cores[core_counter]), 
                                        script_file, 
                                        log_address)
                ret = src.cmd(command)
                with open(cons.TASKSET_OUTPUT_PATH, 'ab') as f: 
                    f.write(ret)
                    f.write("\n")
                    f.flush()

                core_counter += 1
                core_counter %= len(available_cores)