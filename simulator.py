import os
import sys
import signal
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
from mininet.topo import Topo
from mininet.node import RemoteController
from mininet.node import Controller
from mininet.node import OVSSwitch
from mininet.node import Host
from mininet.node import CPULimitedHost
from mininet.node import Node
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.util import custom

import constants as cons
from migration_protocol_handler import get_protocol_messages
from migration_protocol_handler import get_protocol_msg_description
from migration_protocol_handler import get_protocols_first_message
from util import process_dump

from MigrationHandler import MigrationHandler
from MyTopo import MyTopo


# import neptune
neptune_enable = False

def create_neptune_experiment(config):
    if neptune_enable:
        params = {
            'n1-load':config["n1"],
            'n2-load':config["n2"],
            'load': config["load"],
            'protocol':config["protocol"],
            'state_size': config["state_size"]
        }

        neptune.create_experiment(name = "{}-{}".format(protocol, load), params = params)
        neptune.append_tag("load-balance")

def neptune_log_metrics(buff_size, mig_time):
    if neptune_enable:
        neptune.log_metric('buffer', buff_size)
        neptune.log_metric('time', mig_time)



def SIGINT_handler(signum, frame):
    print("Interrupt signal. Exiting ...")
    killall()
    sys.exit(0)

def killall():
    proc2kill = ['myTCPServer', 'ITGSend', 'ITGRecv', 'ITG', 'scapy', 'tcpdump', 'rate_limiter']
    for proc in proc2kill:
        os.system("pkill -f {}".format(proc))

def terminate(signum, frame):
    raise Exception("Run took so long. Restart it!")

def wait_progress(toolbar_width):
    sys.stdout.write("[%s]" % (" " * toolbar_width))
    sys.stdout.flush()
    sys.stdout.write("\b" * (toolbar_width+1))
    for i in range(toolbar_width):
        time.sleep(1) 
        sys.stdout.write("#")
        sys.stdout.flush()
    sys.stdout.write("]\n")

def set_arp(net):
    hosts = ['h{}'.format(i) for i in range(1,6)]

    for host in hosts:
        host_object = net.get(host)
        for host2 in hosts:
            if host != host2:
                host2_object = net.get(host2)
                dst_ip = host2_object.IP()
                dst_mac = host2_object.MAC()
                host_object.cmd('arp', '-s', dst_ip, dst_mac)

def setup_tc_police(config):
    for iface in ['s3-eth1', 's4-eth1', 's5-eth1']:

        if iface == "s3-eth1": # between the main switch and the mig switch
            delay = config['switch_delay']
        elif iface == "s4-eth1": # source controller 
            delay = config['csrc_delay'] 
        else: 
            delay = config['cdst_delay'] 

        delay = str(delay) + "ms"

        command = "bash ./tc-police.sh {} {} {} {} {}".format(
            iface,
            cons.TC_RATE_LIMIT,
            cons.TC_BURST_SIZE,
            delay,
            cons.TC_NETEM_LIMIT,
        )

        print(command)
        ret = os.system(command)
        if ret != 0: 
            print("Encountered error in setting TC Police for {}".format(iface))


def test(net, config, res_path, exp_id):
    print("Setting up ARP and TC police ...")
    set_arp(net)
    setup_tc_police(config)
    net.pingAll()
    os.system('./disabletso.sh')

    print("Running Migration ...")
    is_finished = MigrationHandler(net, config, res_path, exp_id).migrate()

    if not is_finished:
        return False
    return True
    

def clean_logs_directory():
    os.system('rm -rf {}'.format(cons.LOGS_DIR))
    os.system('mkdir -p {}'.format(cons.LOGS_DIR))
    os.system('mkdir -p {}'.format(cons.HOST_LOGS_DIR))
    os.system('mkdir -p {}'.format(cons.TRAFFIC_RECV_LOGS_DIR))
    os.system('mkdir -p {}'.format(cons.TRAFFIC_SEND_SCRIPT_DIR))
    os.system('mkdir -p {}'.format(cons.TRAFFIC_SEND_LOGS_DIR))


def clean_res_directory(): 
    # os.system('rm -rf results')
    os.system('mkdir -p results')

def setup_experiment_res_directory(config): 
    res_directory = "results/{}/".format(config["name"]) 
    for param in config: 
        res_directory += "{}:{}+".format(param, config[param])
    res_directory = res_directory[:-1]

    os.system("mkdir -p {}".format(res_directory))
    return res_directory

def backup_logs_to_res(res_directory, protocol, i):
    log_copy_path = "{}/logs/{}_{}".format(res_directory, protocol, i+1)
    os.system("mkdir -p {}".format(log_copy_path))
    os.system("cp -r logs {}".format(log_copy_path))
    os.system("rm -r {}/logs/iperf/".format(log_copy_path))

def run_exp(config, exp):
    create_neptune_experiment(config)
    n_resets = 0

    i = 0
    while i < 1: 
        print("------------------------------------------------------")
        clean_logs_directory()
        res_directory = setup_experiment_res_directory(config)
        res_path = "{}/{}.res".format(res_directory, config['protocol'])

        print("Cleaning existing Mininet config ...")
        os.system("mn -c -v output")
        print("Killing all active processes ...")
        killall()

        net = Mininet(
            topo=MyTopo(), 
            host=Host, 
            switch=OVSSwitch,
            controller=lambda name: RemoteController(
                name, 
                ip='127.0.0.1', 
                port=6633
            ),
            autoSetMacs=True, 
            autoStaticArp=False
        )

        net.start()
        if not test(net, config, res_path, exp_id=i+exp+1):
            if n_resets == 2:
                net.stop()
                break
            else:
                n_resets += 1
        else:   
            i += 1

        net.stop()
        backup_logs_to_res(res_directory, config['protocol'], i + exp)
        print("------------------------------------------------------")

    if neptune_enable: 
        neptune.stop()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, SIGINT_handler)
    signal.signal(signal.SIGALRM, terminate)

    clean_res_directory()

    if len(sys.argv) < 3:
        exp_min = 0
        exp_max = 1
    else: 
        exp_min = int(sys.argv[1])
        exp_max = int(sys.argv[2])

    if len(sys.argv) < 4:
        test_name = "default"
    else: 
        test_name = sys.argv[3]

    try:
        ##############################################
        # Exp: Load Heatmap
        ##############################################
        if test_name == "heatmap_src_dst_load":
            configs = {
                'name' : ["heatmap_src_dst_load"],
                'n1': [cons.FULL_CONNECTION_COUNT],
                'n2': [cons.FULL_CONNECTION_COUNT],
                'csrc_load': [0.8, 0.85, 0.9, 0.95, 1, 1.05],
                'cdst_load': [0.8, 0.85, 0.9, 0.95, 1, 1.05],
                'csrc_delay': [1],
                'cdst_delay': [1],
                'switch_delay': [1],
                'protocol': ["Four-phase"],
                'state_size': [0], #range(0, 500, 100)
                'interdept' : ['E'],
            }


        ##############################################
        # Exp: Delay Heatmap
        ##############################################
        elif test_name == "heatmap_src_dst_delay": 
            configs = {
                'name': ['heatmap_src_dst_delay'],
                'n1': [cons.FULL_CONNECTION_COUNT],
                'n2': [cons.FULL_CONNECTION_COUNT],
                'csrc_load': [0.5],
                'cdst_load': [0.5],
                'csrc_delay': range(1,10,2),
                'cdst_delay': range(1,10,2),
                'switch_delay': [0],#list(np.arange(0,1,0.1)) + range(1,10),
                'protocol': ["ERC", "Four-phase"],
                'state_size': [0], #range(0, 500, 100)
                'interdept' : ['E'],
            }

        ##############################################
        # Exp: Load Balancing
        ##############################################
        elif test_name == "load_balancing": 
            configs = {
                'name': ['load_balancing'],
                'n1': [cons.FULL_CONNECTION_COUNT],
                'n2': [cons.FULL_CONNECTION_COUNT],
                'csrc_load': [0.85,0.95,1.05],
                'cdst_load': np.arange(0.5,1.1,0.05),
                'csrc_delay': [1],
                'cdst_delay': [1],
                'switch_delay': [1],#list(np.arange(0,1,0.1)) + range(1,10),
                'protocol': ["ERC", "Four-phase"],
                'state_size': [0], #range(0, 500, 100)
                'interdept' : ['E'],
            }


        ##############################################
        # Exp: Power Saving
        ##############################################
        elif test_name == "power_saving": 
            configs = {
                'name': ['power_saving'],
                'n1': [cons.FULL_CONNECTION_COUNT],
                'n2': [cons.FULL_CONNECTION_COUNT],
                'csrc_load': [0.35, 0.45, 0.55],
                'cdst_load': np.arange(0.5,1.1,0.05),
                'csrc_delay': [1],
                'cdst_delay': [1],
                'switch_delay': [1],#list(np.arange(0,1,0.1)) + range(1,10),
                'protocol': ["ERC", "Four-phase"],
                'state_size': [0], #range(0, 500, 100)
                'interdept' : ['E'],
            }

        
        # #############################################
        # Exp: Control latency reduction
        # #############################################
        elif test_name == "control_latency_reduction": 
            configs = {
                'name': ['control_latency_reduction'],
                'n1': [cons.FULL_CONNECTION_COUNT],
                'n2': [cons.FULL_CONNECTION_COUNT],
                'csrc_load': np.arange(0.5,1.1,0.05),
                'cdst_load': np.arange(0.5,1.1,0.05),
                'csrc_delay': [5,7,9],
                'cdst_delay': [1],
                'switch_delay': [0],#list(np.arange(0,1,0.1)) + range(1,10),
                'protocol': ["ERC", "Four-phase"],
                'state_size': [0], #range(0, 500, 100)
                'interdept' : ['E'],
            }


        ##############################################
        # Exp: state size
        ##############################################
        elif test_name == "state_size": 
            configs = {
                'name': ['state_size'],
                'n1': [cons.FULL_CONNECTION_COUNT],
                'n2': [cons.FULL_CONNECTION_COUNT],
                'csrc_load': [0.8,0.9, 1],
                'cdst_load': [0.8,0.9, 1],
                'csrc_delay': [1],
                'cdst_delay': [1],
                'switch_delay': [1],
                'protocol': ["ERC"],
                'state_size': range(0, 100, 10),
                'interdept' : ['E'],
            }

        ##############################################
        # Exp: Variants
        ##############################################
        elif test_name == "variants": 
            configs = {
                'name': ['variants'],
                'n1': [cons.FULL_CONNECTION_COUNT],
                'n2': [cons.FULL_CONNECTION_COUNT],
                'csrc_load': np.arange(0.7, 1.1, 0.1),
                'cdst_load': np.arange(0.7, 1.1, 0.1),
                'csrc_delay': [1],
                'cdst_delay': [1],
                'switch_delay': [1],
                'protocol': [
                    "ERC",
                    "ERC-M2E-S2M-Var1",
                    "ERC-E2S-S2E-Var2", 
                    "ERC-M2S-E2M-Var3", 
                    "ERC-M2E-E2M-Var4", 
                ],
                'state_size': [50],
                'interdept' : ['E'],
            }

        ##############################################
        # Exp: Variants
        ##############################################
        elif test_name == "variants_state_size": 
            configs = {
                'name': ['variants_state_size'],
                'n1': [cons.FULL_CONNECTION_COUNT],
                'n2': [cons.FULL_CONNECTION_COUNT],
                'csrc_load': [0.9],
                'cdst_load': [0.9],
                'csrc_delay': [1],
                'cdst_delay': [1],
                'switch_delay': [1],
                'protocol': [
                    "ERC",
                    "ERC-M2E-S2M-Var1",
                    "ERC-E2S-S2E-Var2", 
                    "ERC-M2S-E2M-Var3", 
                    "ERC-M2E-E2M-Var4", 
                ],
                'state_size': range(0, 100, 10),
                'interdept' : ['E'],
            }

        
        ##############################################
        # Exp: default
        ##############################################
        elif test_name == "default":
            configs = {
                'name': ['default'],
                'n1': [cons.FULL_CONNECTION_COUNT],
                'n2': [cons.FULL_CONNECTION_COUNT],
                'csrc_load': [1], #[0.8,0.9, 1],
                'cdst_load': [1], #[0.8,0.9, 1],
                'csrc_delay': [1],
                'cdst_delay': [1],
                'switch_delay': [1],
                'protocol': ["ERC"],#, "Simplified-ERC", "4-Phase"],#,"Simplified-ERC", "4-Phase", ],
                'state_size': [0],#,range(0, 10),
                'interdept' : ['C'],
            }

        keys, values = zip(*configs.items())
        permutations_dicts = [dict(zip(keys, v)) for v in itertools.product(*values)]
        
        print("iterating from {} to {}".format(exp_min, exp_max))
        for i in range(exp_min,exp_max):
            for config in permutations_dicts:

                forced_equal_load_exps = [
                    "control_latency_reduction", 
                    "state_size",
                    "variants",
                    "variants_constant",
                    "temp",
                ]

                if config["name"] in forced_equal_load_exps: 
                    if config["csrc_load"] != config["cdst_load"]:
                        continue

                # print(config)
                run_exp(config, exp=i)

    except Exception as exp:
        print(exp)
        traceback.print_exc()
        os.system("mn -c -v output")
        killall()