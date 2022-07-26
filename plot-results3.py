import os
from os import listdir
from os.path import isfile, join
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def parse_seconds(time_stamp):
    time_stamp = time_stamp.split(":")
    time = 0
    for i in range(len(time_stamp)):
        time += int(time_stamp[i]) * 60 ** (len(time_stamp) - i - 1)
    return time

def parse_time(time_stamp):
    print(time_stamp)
    time, micros = time_stamp.split(".")
    return parse_seconds(time) + int(micros) / 1000000

def parse_line(line):
    time_stamp_end = line.find("]")
    time_stamp_start = line.find("[")
    time_stamp = line[time_stamp_start+1:time_stamp_end]
    time = parse_time(time_stamp)

    incident = line[time_stamp_end+2:]
    if not incident.startswith("["):
        return None
    
    incident_type = incident[1:incident.find("]")]
    incident_split = incident.split(" ")
    if len (incident_split) < 3:
        return None 

    command = incident_split[1] 
    dst = incident_split[3]

    if incident_type == "SENT":
        incident_type = "SEND"

    return time, incident_type, command, dst

plot_counter = 1 
path = "/home/faridzandi/git/Controller-Load-Migration-SDN/protocols/results/temp/"

for setting in os.listdir(path): 
    setting_path = path + setting + "/logs/"

    params_list = setting.split("+")
    params_dict = {}
    for param in params_list: 
        s = param.split(":")
        key = s[0]
        value = None
        try: 
            value = float(s[1])
        except: 
            value = s[1]

        params_dict[key] = value


    for exp in os.listdir(setting_path): 
        if exp.startswith("."):
            continue
        
        exp_path = setting_path + exp + "/"
        exp_path += "logs/hosts/"

        hosts = ["c-dst", "c-src", "mig-switch"]

        messages = {}

        for host in hosts: 
            log_path = exp_path + host + ".serv.out"
            with open(log_path, "r") as f:
                lines = f.readlines()

                for line in lines: 
                    line = line.strip()
                    if line == "":
                        continue
                    
                    parsed_line = parse_line(line)

                    if parsed_line is None:
                        continue
                    
                    time, direction, command, other = parsed_line

                    src = other if direction == "SEND" else host
                    dst = other if direction == "RECV" else host
                    original_command = command
                    command = command + "-" + src + "-" + dst

                    if not command in messages:
                        data = {
                            "command": original_command,
                            "to": src,
                            "from": dst,
                            "sent": time if direction == "SEND" else None,
                            "received": time if direction == "RECV" else None
                        }
                        messages[command] = data
                    else:
                        if direction == "SEND":
                            messages[command]["sent"] = time
                        else:
                            messages[command]["received"] = time
            
        host_to_x = {
            "c-dst": 300,
            "c-src": 100,
            "mig-switch": 200
        }     

        min_time = 10000000000000
        max_time = 0 

 
        # if not params_dict["protocol"] == "ERC" or not params_dict["csrc_load"] == 1:
            # continue

        # print(params_dict["protocol"])

        if params_dict["protocol"] == "ERC":
            buffer_start_time = messages["role_reply-c-dst-mig-switch"]["received"]
            buffer_end_time = messages["role_reply2-c-dst-mig-switch"]["received"]
            plt.plot([300,300], [buffer_start_time, buffer_end_time], color="red", linewidth=5)

        # del messages["controller_status1-c-dst-mig-switch"]
        # del messages["controller_status2-c-dst-mig-switch"]

        for command in messages:
            x1 = host_to_x[messages[command]["from"]]
            x2 = host_to_x[messages[command]["to"]]

            y1 = messages[command]["sent"]
            y2 = messages[command]["received"]

            if y1 is not None:
                min_time = min(min_time, y1)
            if y2 is not None:
                max_time = max(max_time, y2)

            label = messages[command]["command"]
            label = "{} ({} ms)".format(label, 
                                        int((y2 - y1) * 1000))

            plt.plot([x1, x2], [y1, y2], color="black")
            plt.text((x1 + x2) / 2 - len(label) * 1.3 , 
                    (y1 + y2) / 2, 
                    label)

        for x in [100, 200, 300]:
            plt.plot([x, x], [min_time, max_time], color="black")

        print("plotting", exp)
        plt.gca().invert_yaxis()
        plt.savefig("plots/protocols/{}-{}-{}.png".format(
            params_dict["protocol"],params_dict["csrc_load"], plot_counter), dpi=300, bbox_inches='tight')
        plot_counter += 1
        plt.clf()

    
    