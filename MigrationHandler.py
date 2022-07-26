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

from TrafficGenerator import TrafficGenerator


def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()


class MigrationHandler:
    def __init__(self, net, config, res_path, exp_id): 
        
        self.net = net
        self.config = config
        self.res_path = res_path
        self.exp_id = exp_id
        
        self.src_ctrlr = net.get("h4")
        self.dst_ctrlr = net.get("h5")
        self.mig_switch = net.get("h3")
        self.running_processes = [] 
        self.ips_pickle, self.ports_pickle = self.get_ip_port_pickles()


    def kill_running_processes(self):
        for server in self.running_processes:
            kill(server.pid)

    def get_ip_port_pickles(self):

        ips = {"c-src": self.src_ctrlr.IP(),
                "c-dst": self.dst_ctrlr.IP(),
                "mig-switch": self.mig_switch.IP()}

        port_offset = self.exp_id * 3
        server_ports = {"c-src": 2222 + port_offset,
                        "c-dst": 2223 + port_offset,
                        "mig-switch": 2224 + port_offset}

        ips_pickle_address = "/tmp/ips.pickled"
        ports_pickle_address = "/tmp/ports.pickled"

        with open(ips_pickle_address, 'wb') as ips_file:
            pickle.dump(ips, ips_file)
        with open(ports_pickle_address, 'wb') as ports_file:
            pickle.dump(server_ports, ports_file)

        return ips_pickle_address, ports_pickle_address

    def run_tcpdump(self):
        proc = subprocess.Popen(
            "taskset -c {} nohup tcpdump -l -i s5-eth1 dst portrange 4445 > {} &".format(
                cons.CORES['TCPDump'], 
                cons.DUMP_FILE
            ), 
            shell=True
        )
        return proc

    def run_server(self, host, name):
        serv = host.popen("python2 myTCPServer.py {} {} {} {} {} {}".format(
            name, 
            self.config['protocol'], 
            self.config['state_size'], 
            self.ips_pickle, 
            self.ports_pickle,
            2*(self.config['csrc_delay'] + self.config['cdst_delay']),
        ))
        return serv  

    def wait_for_connection(self):
        roles = ['c-src', 'c-dst', 'mig-switch']
        while True:
            all_ok = True 
            for role in roles: 
                if not os.path.exists(cons.CONNECTION_DONE_PATH[role]):
                    all_ok = False
                    break
            if all_ok: 
                return
            time.sleep(0.1)

    def notify_ok_to_initiate(self):
        with open(cons.OK_TO_INITIATE_PATH, 'wb') as f:
            f.write(str(datetime.datetime.now().time()))            
            f.flush()

    def initiate_and_wait(self):
        while not os.path.exists(cons.FINISH_TIME):
            time.sleep(0.1)
        return

    def log_results(self, buff_size, mig_time, downtime, 
                    protocol_start, phase_finish):

        print(self.config)
        print("Exp id: {}, Buffer: {}, Migration Time:{}, Downtime: {}".format(
            self.exp_id, 
            buff_size, 
            mig_time, 
            downtime
        ))
        
        with open(self.res_path, 'a+') as f:
            f.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                mig_time, buff_size, downtime,
                protocol_start,
                phase_finish[0],
                phase_finish[1],
                phase_finish[2],
                phase_finish[3]
            ))

        from simulator import neptune_log_metrics
        neptune_log_metrics(buff_size, mig_time)

    
    def read_from_file(self, file):
        with open(file, 'rb') as f:
            value = f.readline().strip()
        return value

    def get_processing_time(self):
        start_time = self.read_from_file(cons.START_TIME)
        finish_time = self.read_from_file(cons.FINISH_TIME)

        start = datetime.datetime.strptime(start_time, cons.TIME_PATTERN)
        finish = datetime.datetime.strptime(finish_time, cons.TIME_PATTERN)

        return (finish - start).total_seconds()
    
    def get_downtime(self):
        start_time = self.read_from_file(cons.BUFFER_AT_START)
        finish_time = self.read_from_file(cons.BUFFER_AT_FINISH)

        start = datetime.datetime.strptime(start_time, cons.TIME_PATTERN)
        finish = datetime.datetime.strptime(finish_time, cons.TIME_PATTERN)

        return (finish - start).total_seconds()


    def measure_mig_time(self):
        t = timeit.Timer(functools.partial(self.initiate_and_wait))
        try:
            signal.alarm(100)
            mig_time = t.timeit(1) # timeit is not longer in use for our simulations
            mig_time = self.get_processing_time()
            signal.alarm(0)
            return mig_time
        except Exception as exc:
            print("The protocol didn't finish in time. Reason: {}".format(exc))
            self.kill_running_processes()
            from simulator import neptune_log_metrics
            neptune_log_metrics(0, 0)
            signal.alarm(0)
            return 0
        
    def migrate(self):
        tcpdump_proc = self.run_tcpdump()
        serv_a = self.run_server(self.mig_switch, "mig-switch")
        serv_b = self.run_server(self.src_ctrlr, "c-src")
        serv_c = self.run_server(self.dst_ctrlr, "c-dst")
        self.running_processes = [tcpdump_proc, serv_a, serv_b, serv_c]

        print("Waiting for the servers to set up their connections ...")
        self.wait_for_connection()

        print("Setting up background traffic generators ...")
        TrafficGenerator(self.net, self.config).start()

        print("Waiting ...")
        time.sleep(5)

        print("Initiating the protocol ...")
        self.notify_ok_to_initiate()
        mig_time = self.measure_mig_time()
        if mig_time == 0: 
            return False
    
        time.sleep(2)
        tcpdump_proc.kill()
        time.sleep(2)

        protocol_start = self.read_from_file(cons.START_TIME)
        start_time = self.read_from_file(cons.BUFFER_AT_START)
        finish_time = self.read_from_file(cons.BUFFER_AT_FINISH)
        buff_size = process_dump(start_time, finish_time)
        downtime = self.get_downtime()

        phase_finish = [0] * 4
        for i in range(4):
            try:
                phase_finish[i] = self.read_from_file(cons.PHASE_FINISH[i])
            except IOError:
                phase_finish[i] = 0

        self.log_results(buff_size, mig_time, downtime, protocol_start, phase_finish)
        
        self.dst_ctrlr.popen("./logifconf.sh dst_ctrl")
        self.src_ctrlr.popen("./logifconf.sh src_ctrl")
        self.mig_switch.popen("./logifconf.sh mig-switch")
        os.system("ifconfig > {}/ifconfig.log".format(cons.LOGS_DIR))

        self.kill_running_processes()
        return True

