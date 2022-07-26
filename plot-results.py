from os import listdir
from os.path import isfile, join
import numpy as np
import matplotlib.pyplot as plt

protocols = ["ERC", "Four-phase"]#, "Simplified-ERC"]
past_results = "past-results/"
plots_dir = "plots"
results_dirs = []#["{}/{}".format(past_results, f) for f in listdir(past_results)] 
results_dirs.append("results")
results_dirs.sort()
for results_dir in results_dirs: 
    all_results = {} 
    for protocol in protocols: 
        all_results[protocol] = {'load':[], 'time':[], 'buffer':[]}


    load_dirs = [f for f in listdir(results_dir)]
    load_dirs.sort()
    for load_dir in load_dirs: 
        load = load_dir.split("-")[-3]
        

        for protocol in protocols: 
            try: 
                times = []
                buffers = [] 
                file_path = "./{}/{}/{}.res".format(results_dir, load_dir, protocol)
                with open(file_path, "r") as file:
                    for line in file.readlines():
                        line = line.strip()
                        time, buffer, downtime = line.split("\t")
                        if buffer == 0: 
                            continue
                        times.append(time)
                        buffers.append(buffer)
                times = np.array(times, dtype=np.float32)
                buffers = np.array(buffers, dtype=np.float32)
                all_results[protocol]["load"].append(float(load))
                all_results[protocol]["time"].append(float(np.mean(times)))
                all_results[protocol]["buffer"].append(int(np.mean(buffers)))
            except Exception as e: 
                print(str(e))

    for measure in ["time", "buffer"]:
        for protocol in protocols: 
            plt.plot(all_results[protocol]["load"], all_results[protocol][measure], label = protocol)
        
        plt.legend()
        plt.title(results_dir)
        plt.ylabel(measure)
        plt.xlabel('Load')
        name = results_dir.split("/")[-1]
        plt.savefig('{}/{}-{}.png'.format(plots_dir, name, measure))
        plt.clf()
