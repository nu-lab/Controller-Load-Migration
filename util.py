import subprocess
import string
import constants as cons
import os
import csv
import time
from datetime import datetime


def get_packets_count(switch="s1", target_port="port20"):
    p = subprocess.Popen(['ovs-ofctl', 'dump-ports', switch], stdout=subprocess.PIPE)
    stdout = p.communicate()[0]
    # print 'STDOUT:{}'.format(stdout)
    lines = stdout.split("\n")
    for i in range(len(lines)):
        line = lines[i]
        if line.find(":") > 0:
            port_no = line.split(":")[0].translate(None, string.whitespace)
            # print("port number is: {}\nand the line is: {}".format(port_no, line))
            if port_no == target_port:
                rx_packets = int(line.split(":")[1].split(",")[0].split("=")[1].strip())
                return rx_packets

    # p = subprocess.Popen(['sudo', 'ovs-ofctl', 'dump-aggregate', switch], stdout=subprocess.PIPE)
    # stdout = p.communicate()[0]
    # print 'STDOUT:{}'.format(stdout)
    # lines = stdout.split("\n")
    # packets_count = int(lines[0].split(" ")[3].split("=")[1])
    # print("pkt_count", packets_count)
    # return packets_count


"""
this function reads the dump file after the experiment is done to find out the
number of the received packets between two intervals (i.e., the buffering time)
accordingly, we use this number as the number of supposedly bufferred messages
"""


def process_dump(start_time, finish_time):
    # print("DUMP", start_time, finish_time)
    # res = subprocess.check_output(["sed", "-rne '/{}/,/{}/ p' {}".format(start_time, finish_time, cons.DUMP_FILE)])
    # command = ["awk", "-v", "from='{}'".format(start_time), "-v", "to='{}'".format(finish_time), '$1>=from && $1<=to', cons.DUMP_FILE]
    # res = subprocess.check_output(command)
    # while not os.path.exists(cons.DUMP_FILE):
    #     time.sleep(0.1)

    # this is for parsing scapy's output
    # count = 0
    # with open(cons.DUMP_FILE, 'r') as dump:
    #     reader = csv.reader(dump)
    #     for line in reader:
    #         timestamp = line[0]
    #         if timestamp>=start_time and timestamp<=finish_time:
    #             count = count + 1
    # return count

    # this is for parsing tcpdump's output
    count = 0
    pattern = '%H:%M:%S.%f'
    with open(cons.DUMP_FILE, 'r') as dump:
        reader = csv.reader((line.replace('\0', '') for line in dump), delimiter=' ')
        next(reader)  # skip the first two lines
        next(reader)
        start = datetime.strptime(start_time, pattern)
        finish = datetime.strptime(finish_time, pattern)
        for line in reader:
            try:
                timestamp = line[0]
                timestamp = datetime.strptime(timestamp, pattern)
                if timestamp >= start and timestamp <= finish:
                    count = count + int(line[-1]) #count bytes
                elif timestamp > finish:
                    break
            except Exception as e:
                print(str(e))
                # break  # this is a malformed line at the end of the file (certainly after the migration is finished)
    return count


# print(process_dump("17:16:24.686032","17:16:25.254332"))