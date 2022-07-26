import os
from os import listdir
from os.path import isfile, join
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import seaborn as sns
import datetime 

time_pattern = '%H:%M:%S.%f'
plot_scales = ['log', 'linear']
protocols = ["ERC", "4-Phase", "Simplified-ERC"] + \
            ["ERC-M2E-E2M-Var4", "ERC-M2S-E2M-Var3", 
            "ERC-E2S-S2E-Var2", "ERC-M2E-S2M-Var1"]
past_results = "results/"
plots_dir = "plots"
reload_results = True
# reload_results = False
running_exp = "all"

def get_time(time_str):
    try:
        return datetime.datetime.strptime(time_str, time_pattern)
    except:
        return 0

def get_seconds(time, start):
    if time == 0:
        return 0
    else:
        return (time - start).total_seconds()


def parse_results(line):
    line = line.strip()
    line_split = line.split("\t")
    result = {}
    result["time"] = line_split[0]
    result["buffer"] = line_split[1]
    result["downtime"] = line_split[2]
    result["start_time"] = get_time(line_split[3])
    result["phase_1"] = get_time(line_split[4])
    result["phase_2"] = get_time(line_split[5])
    result["phase_3"] = get_time(line_split[6])
    result["phase_4"] = get_time(line_split[7])

    return result


def save_plot_clf(base_path):
    plt.savefig("{}.pdf".format(base_path), dpi=300, bbox_inches='tight')
    plt.savefig("{}.png".format(base_path), dpi=300, bbox_inches='tight')
    plt.clf()


def set_x_axis_percentage(ax):
    def format_func(value, tick_number):
        return "{:.0f}%".format(value*100)

    ax.xaxis.set_major_formatter(plt.FuncFormatter(format_func))


def get_ylabel(mesure):
    if mesure == "time":
        return "Time (s)"
    elif mesure == "buffer":
        return "Buffer size (bytes)"
    elif mesure == "downtime":
        return "Downtime (s)"


def load_data(results_dir):
    columns=[
        'time', 'buffer', 'downtime',
        'phase_1', 'phase_2', 
        'phase_3', 'phase_4',
        'n1', 'n2', 'interdept', 'state_size',
        'switch_delay', 'csrc_delay', 'cdst_delay',
        'csrc_load', 'cdst_load','protocol']

    df = pd.DataFrame(columns = columns)
    
    load_dirs = [f for f in listdir(results_dir)]
    load_dirs.sort()
    for load_dir in load_dirs: 

        # convert the folder name to a dict
        # containing the experiment parameters
        params_list = load_dir.split("+")
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

        for protocol in protocols: 
            try: 
                file_path = "./{}{}/{}.res".format(
                    results_dir, 
                    load_dir, 
                    protocol
                )

                with open(file_path, "r") as file:
                    for line in file.readlines():

                        result = parse_results(line)

                        if int(result["buffer"]) > 1000000: 
                            continue

                        new_row = params_dict.copy()
                        new_row['time'] =  float(result["time"]) 
                        new_row['buffer'] =  float(result["buffer"])
                        new_row['downtime'] =  float(result["downtime"])  

                        new_row['phase_1'] = get_seconds(
                            result["phase_1"], result["start_time"]
                        )
                        new_row['phase_2'] = get_seconds(
                            result["phase_2"], result["start_time"]
                        )
                        new_row['phase_3'] = get_seconds(
                            result["phase_3"], result["start_time"]
                        )
                        new_row['phase_4'] = get_seconds(
                            result["phase_4"], result["start_time"]
                        )

                        new_row['protocol'] = protocol

                        df = df.append(new_row, ignore_index=True)

            except Exception as e: 
                pass
                # print(str(e))

    # print(df)
    # df = df.drop(df[(df['buffer'] == 0)].index) 
    return df 

results_dirs = []
results_dirs += ["{}{}/".format(past_results, f) for f in listdir(past_results)] 
results_dirs.sort()


for results_dir in results_dirs:
    print("Loading data from {}".format(results_dir))

    if running_exp != "all": 
        if results_dir != running_exp: 
            continue 

    # very bad way to do this
    name = results_dir.split("/")[-2]
    pickle_path = "pickles/{}.pickle".format(name)

    if reload_results:
        df = load_data(results_dir)
        print("Saving data to {}".format(pickle_path))
        df.to_pickle(pickle_path)
    else:
        print("Loading pickle from {}".format(pickle_path))
        df = pd.read_pickle(pickle_path)
    
    plot_dir = "plots/{}".format(name)
    os.system("mkdir -p {}".format(plot_dir))
    print("Saving plots to {}".format(plot_dir))

    # ----------------------------------------------------#
    # ----------------------------------------------------#
    # ----------------------------------------------------#
    
    if name == "heatmap_src_dst_load":

        base_path = "{}/phase".format(plot_dir)
        print("saving to {}".format(base_path))

        t = df 
        t = t[t['csrc_load'] == 0.9]
        t = t[t['cdst_load'] == 0.9]

        order = ["4-Phase", "Simplified-ERC", "ERC"]
        colors = ["#006600", "#009900", "#00CC00", "#00FF00"] 

        bar4 = sns.barplot(y="protocol",  x="phase_4", 
                           order = order, orient = "h", 
                           data=t, color=colors[0], ci=None)

        bar3 = sns.barplot(y="protocol",  x="phase_3", 
                           order = order, orient = "h", 
                           data=t, color=colors[1], ci=None)

        bar2 = sns.barplot(y="protocol",  x="phase_2", 
                           order = order, orient = "h", 
                           data=t, color=colors[2], ci=None)

        bar1 = sns.barplot(y="protocol",  x="phase_1", 
                           order = order, orient = "h", 
                           data=t, color=colors[3], ci=None)

        

        for i in [3, 5, 7, 8]:
            bar1.patches[i].set_hatch('//')


        new_value = .35
        for patch in bar1.patches:
            current_width = patch.get_height()
            diff = current_width - new_value

            # we change the bar width
            patch.set_height(new_value)

            # we recenter the bar
            patch.set_y(patch.get_y() + diff * .5)

        bar1.set_xlabel("Time")

        handles = [] 
        for i in range(4): 
            handles.append(mpatches.Patch(color=colors[i], label="Phase " + str(4 - i)))
        plt.legend(handles=handles)

        save_plot_clf(base_path)
        
    # ----------------------------------------------------#
    # ----------------------------------------------------#
    # ----------------------------------------------------#

    if name == "heatmap_src_dst_load":
        for p in ["ERC", "4-Phase", "Simplified-ERC"]:
            for metric in ["time", "buffer", "downtime"]:
                
                base_path = "{}/{}-{}-{}".format(
                    plot_dir, name, p, metric
                )
                print("saving to {}".format(base_path))

                def agg(data):
                    if metric == "buffer":
                        return int(np.mean(data) / 1000)
                    else: 
                        return int(np.mean(data) * 1000)

                def get_fmt(): 
                    if metric == "buffer": 
                        return ".0f"
                    else: 
                        return ".0f"

                    
                t = df[df["protocol"] == p]
                pdf = t.pivot_table(
                    index="csrc_load",
                    columns="cdst_load", 
                    values=metric, aggfunc=agg
                )
                ax = sns.heatmap(pdf, annot=True, 
                                 fmt=get_fmt(),
                                 cmap="rocket_r",
                                 cbar=True)


                plt.tick_params(
                    axis='both', which='major', 
                    labelsize=10, 
                    labelbottom = False, bottom=False, 
                    labeltop=True, top = True)
                
                ax.xaxis.set_label_position('top')
                ax.set_xlabel("Destination Load")
                ax.set_ylabel("Source Load")

                save_plot_clf(base_path)
                plt.clf()

    # ----------------------------------------------------#
    # ----------------------------------------------------#
    # ----------------------------------------------------#

    if name == "heatmap_src_dst_delay":
        for p in ["ERC", "4-Phase", "Simplified-ERC"]:
            for metric in ["time", "buffer", "downtime"]:
                
                base_path = "{}/{}-{}-{}".format(
                    plot_dir, name, p, metric
                )
                print("saving to {}".format(base_path))

                def agg(data):
                    if metric == "buffer":
                        return int(np.mean(data))
                    else: 
                        return int(np.mean(data)*1000)

                def get_fmt(): 
                    if metric == "buffer": 
                        return ".0f"
                    else: 
                        return ".0f"

                t = df[df["protocol"] == p]
                pdf = t.pivot_table(
                    index="csrc_delay", 
                    columns="cdst_delay", 
                    values=metric, aggfunc=agg
                )
                ax = sns.heatmap(pdf, annot=True, 
                                 fmt=get_fmt(),
                                 cmap="rocket_r",
                                 cbar=True)

                plt.tick_params(
                    axis='both', which='major', 
                    labelsize=10, labelbottom = False, 
                    bottom=False, top = True, 
                    labeltop=True)

                ax.xaxis.set_label_position('top')
                ax.set_xlabel("Destination Delay (ms)")
                ax.set_ylabel("Source Delay (ms)")

                save_plot_clf(base_path)
                plt.clf()
    
    # ----------------------------------------------------#
    # ----------------------------------------------------#
    # ----------------------------------------------------#
        
    if name == "control_latency_reduction":
        t = df
        t = t[t['cdst_load'] < 1.09]
        t = t[t['cdst_load'] > 0.74]
        t = t.drop(t[(t['csrc_delay'] == 7.0)].index)
        t = t.drop(t[(t['protocol'] == "ERC")].index)
        t = t.replace("Simplified-ERC", "ERC")

        # combining the protocol name and the delay to make
        # the hue variable
        def rep(row):
            res =   "{}, Src Delay: {} ms".format(
                        row['protocol'], 
                        row['csrc_delay']
                    )
            return res

        t['Protocol'] = t[['protocol', 'csrc_delay']].apply(
            (rep), axis = 1
        )
        
        for scale in plot_scales:
            for metric in ["time", "buffer", "downtime"]:

                base_path = "{}/{}-{}-{}".format(
                    plot_dir, name, metric, scale
                )
                print("saving to {}".format(base_path))

                sns.set_style("ticks")
                ax = sns.lineplot(
                    data=t, hue='Protocol', estimator=np.mean,
                    x='cdst_load', y=metric, 
                    style="Protocol", legend="full",
                    palette=['#FF7777', '#AA0000', 
                             '#77FF77', '#007700'],
                    markers=["o", "^", "s", "D"],  
                )
                ax.set(yscale=scale)
                ax.set_xlabel("Destination Load")
                ax.set_ylabel(get_ylabel(metric))
                set_x_axis_percentage(ax)

                left_annot = [] 
                if metric == "buffer":
                    left_annot = []
                elif metric == "downtime":
                    left_annot = []
                else:
                    left_annot = [0,1,2,3]
                
                for i in left_annot: 
                    y = ax.lines[i].get_ydata()
                    if len(y)>0:
                        if metric == "buffer":
                            annot = f'{int(y[0]):d}B'
                        else: 
                            annot = f'{y[0]:.3f}s'
                        
                        ax.annotate(
                            annot, xy=(-0.01,y[0]), 
                            xycoords=('axes fraction', 
                                      'data'), 
                            ha='right', va='center', 
                            color=ax.lines[i].get_color()
                        )

                for l in [ax.lines[1], ax.lines[3]]:
                    y = l.get_ydata()
                    if len(y)>0:
                        if metric == "buffer":
                            val = int(y[-1]//1000) 
                            annot = f'{val:d}KB'
                        else: 
                            annot = f'{y[-1]:.2f}s'
                        
                        ax.annotate(
                            annot, xy=(1.02,y[-1]), 
                            xycoords=('axes fraction', 
                                      'data'), 
                            ha='left', va='center', 
                            color=l.get_color()
                        )

                

                plt.grid(True, which="both", linestyle='--')
                save_plot_clf(base_path)
            
    # ----------------------------------------------------#
    # ----------------------------------------------------#
    # ----------------------------------------------------#

    if name == "load_balancing":
        t = df[df['cdst_load'] < 1.04]
        t = t[t['cdst_load'] > 0.74] 

        t = t.drop(t[(t['csrc_load'] == 0.85)].index)
        t = t.drop(t[(t['protocol'] == "ERC")].index)
        t = t.replace("Simplified-ERC", "ERC")

        def rep(row):
            res =   "{}, Src Load: {}%".format(
                        row['protocol'], 
                        int(row['csrc_load'] * 100) 
                    )
            return res

        t['Protocol'] = t[['protocol', 'csrc_load']].apply(
            (rep), axis = 1
        )
        
        all_hues = t['Protocol'].unique()
        all_hues.sort()
        print(all_hues)

        for scale in plot_scales:
            for metric in ["time", "buffer", "downtime"]:
                
                base_path = "{}/{}-{}-{}".format(
                    plot_dir, name, metric, scale
                )
                print("saving to {}".format(base_path))

                sns.set_style("ticks")

                ax = sns.lineplot(
                    data=t, hue='Protocol', estimator=np.mean,
                    x='cdst_load', y=metric, 
                    style="Protocol", legend="full",
                    palette=['#FF7777', '#AA0000', 
                             '#77FF77', '#007700'],
                    markers=["o", "^", "s", "D"],
                    hue_order=all_hues,
                    sort=True,  
                )

                ax.set(yscale=scale)
                ax.set_xlabel("Destination Load")
                ax.set_ylabel(get_ylabel(metric))
                set_x_axis_percentage(ax)


                for l in ax.lines:
                    y = l.get_ydata()
                    if len(y)>0:
                        if metric == "buffer":
                            val = int(y[-1]//1000) 
                            annot = f'{val:d}KB'
                        else: 
                            annot = f'{y[-1]:.2f}s'
                        
                        ax.annotate(
                            annot, xy=(1.01,y[-1]), 
                            xycoords=('axes fraction', 
                                      'data'), 
                            ha='left', va='center', 
                            color=l.get_color()
                        )

                left_annot = [] 
                if metric == "buffer":
                    left_annot = [0,1,3]
                elif metric == "downtime":
                    left_annot = [0,1,3]
                else:
                    left_annot = [1,3]
                
                for i in left_annot: 
                    y = ax.lines[i].get_ydata()
                    if len(y)>0:
                        if metric == "buffer":
                            val = int(y[0]//1000) 
                            annot = f'{val:d}KB'
                        else: 
                            annot = f'{y[0]:.2f}s'
                        
                        ax.annotate(
                            annot, xy=(-0.01,y[0]), 
                            xycoords=('axes fraction', 
                                      'data'), 
                            ha='right', va='center', 
                            color=ax.lines[i].get_color()
                        )
                


                plt.grid(True, which="both", linestyle='--')
                save_plot_clf(base_path)
    
    # ----------------------------------------------------#
    # ----------------------------------------------------#
    # ----------------------------------------------------#

    if name == "power_saving":
        t = df[df['cdst_load'] < 1.06]
        t = t[t['cdst_load'] > 0.74] 

        t = t.drop(t[(t['csrc_load'] == 0.45)].index)
        t = t.drop(t[(t['protocol'] == "ERC")].index)
        t = t.replace("Simplified-ERC", "ERC")

        def rep(row):
            res =   "{}, Src Load: {}%".format(
                        row['protocol'], 
                        int(row['csrc_load'] * 100) 
                    )
            return res

        t['Protocol'] = t[['protocol', 'csrc_load']].apply(
            rep, axis = 1
        )

        all_hues = t['Protocol'].unique()
        all_hues.sort()

        for scale in plot_scales:
            for metric in ["time", "buffer", "downtime"]:
                
                base_path = "{}/{}-{}-{}".format(
                    plot_dir, name, metric, scale
                )
                print("saving to {}".format(base_path))

                sns.set_style("ticks")

                ax = sns.lineplot(
                    data=t, hue='Protocol', estimator=np.mean,
                    x='cdst_load', y=metric, 
                    style="Protocol", legend="full",
                    palette=['#FF7777', '#AA0000', 
                             '#77FF77', '#007700'],
                    markers=["o", "^", "s", "D"],
                    hue_order=all_hues,
                    sort=True,  
                )

                ax.set(yscale=scale)
                ax.set_xlabel("Destination Load")
                ax.set_ylabel(get_ylabel(metric))
                set_x_axis_percentage(ax)

                right_annot = [] 
                if metric == "buffer":
                    right_annot = [1]
                elif metric == "downtime":
                    right_annot = [1]
                else:
                    right_annot = [1, 3]

                for i in right_annot: 
                    y = ax.lines[i].get_ydata()
                    if len(y)>0:
                        if metric == "buffer":
                            annot = f'{int(y[-1]):d}B'
                        else: 
                            annot = f'{y[-1]:.2f}s'
                        
                        ax.annotate(
                            annot, xy=(1.01,y[-1]), 
                            xycoords=('axes fraction', 
                                      'data'), 
                            ha='left', va='center', 
                            color=ax.lines[i].get_color()
                        )

                left_annot = [] 
                if metric == "buffer":
                    left_annot = [0,2]
                elif metric == "downtime":
                    left_annot = [1,3]
                else:
                    left_annot = [1]
                
                for i in left_annot: 
                    y = ax.lines[i].get_ydata()
                    if len(y)>0:
                        if metric == "buffer":
                            annot = f'{int(y[0]):d}B'
                        else: 
                            annot = f'{y[0]:.2f}s'
                        
                        ax.annotate(
                            annot, xy=(-0.01,y[0]), 
                            xycoords=('axes fraction', 
                                      'data'), 
                            ha='right', va='center', 
                            color=ax.lines[i].get_color()
                        )
                
    

                plt.grid(True, which="both", linestyle='--')
                save_plot_clf(base_path)
    
    # ----------------------------------------------------#
    # ----------------------------------------------------#
    # ----------------------------------------------------#

    if name == "state_size": 
        
        t = df
        # t = t[t['cdst_load'] < 1.06]
        # t = t[t['cdst_load'] > 0.74] 

        # t = t.drop(t[(t['csrc_load'] == 0.8)].index)

        def rep(row):
            res =   "Src Load: {}%".format(
                        int(row['csrc_load'] * 100) 
                    )
            return res

        t['csrc_load'] = t[['csrc_load']].apply(
            rep, axis = 1
        )

        for scale in plot_scales:
            for metric in ["time", "buffer", "downtime"]:

                base_path = "{}/{}-{}-{}".format(
                    plot_dir, name, metric, scale
                )
                print("saving to {}".format(base_path))

                sns.set_style("ticks")

                ax = sns.lineplot(
                    data=t, hue='csrc_load', estimator=np.mean,
                    x='state_size', y=metric, 
                    style="csrc_load", legend="full",
                    palette=['#77FF77', '#008800', "#000000"], 
                    markers=["o", "^", "^"],
                    # hue_order=all_hues,
                    # sort=True,  
                )

                ax.set(yscale=scale)
                ax.set_xticks(range(0,100,10))
                ax.set_xlabel("State Transfer Time (ms)")
                ax.set_ylabel(get_ylabel(metric))

                def format_func(value, tick_number):
                    return str(int(value*4))

                ax.xaxis.set_major_formatter(plt.FuncFormatter(format_func))


                plt.tick_params(
                    axis='both', which='major', 
                    labelsize=10, 
                    labelbottom = True, bottom=True, 
                    labeltop=False, top = False)
                
                right_annot = [] 
                if metric == "buffer":
                    right_annot = [0,1,2]
                elif metric == "downtime":
                    right_annot = [0,1,2]
                else:
                    right_annot = [0,1,2]

                for i in right_annot: 
                    y = ax.lines[i].get_ydata()
                    if len(y)>0:
                        if metric == "buffer":
                            val = int(y[-1]//1000) 
                            annot = f'{val:d}KB'
                        else: 
                            annot = f'{y[-1]:.2f}s'
                        
                        ax.annotate(
                            annot, xy=(1.01,y[-1]), 
                            xycoords=('axes fraction', 
                                      'data'), 
                            ha='left', va='center', 
                            color=ax.lines[i].get_color()
                        )

                left_annot = [] 
                if metric == "buffer":
                    left_annot = [0,1,2]
                elif metric == "downtime":
                    left_annot = [0,1,2]
                else:
                    left_annot = [1]
                
                for i in left_annot: 
                    y = ax.lines[i].get_ydata()
                    if len(y)>0:
                        if metric == "buffer":
                            val = int(y[0]//1000) 
                            annot = f'{val:d}KB'
                        else: 
                            annot = f'{y[0]:.2f}s'
                        
                        ax.annotate(
                            annot, xy=(-0.01,y[0]), 
                            xycoords=('axes fraction', 
                                      'data'), 
                            ha='right', va='center', 
                            color=ax.lines[i].get_color()
                        )

                plt.grid(True, which="both", linestyle='--')
                save_plot_clf(base_path)

    # ----------------------------------------------------#
    # ----------------------------------------------------#
    # ----------------------------------------------------#

    if name == "variants": 

        for metric in ["downtime", "time", "buffer"]:
            base_path = "{}/{}-{}".format(
                plot_dir, name, metric
            )
            print("saving to {}".format(base_path))

            ax = sns.barplot(
                data=t, 
                x='csrc_load', 
                y=metric, 
                hue='protocol', 
                estimator=np.mean,
                errwidth=0
            )
            ax.set_xlabel("Source & Destination Load")
            ax.set_ylabel(get_ylabel(metric))

            for tick in ax.get_xticklabels():
                t = tick.get_text()
                val = int(float(t) * 100)
                tick.set_text(f"{val:d}%")
            ax.set_xticklabels(ax.get_xticklabels())


            def get_fmt(metric):
                if metric == "time":
                    return "%.2f"
                elif metric == "buffer":
                    return "%d"
                else:
                    return "%.2f"
            for c in ax.containers: 
                labels = ax.bar_label(c, padding=3, fmt=get_fmt(metric))
                for label in labels:
                    if metric == "buffer":
                        val = str(int(label.get_text())//1000)
                        label.set_text(val + "KB")
                    label.set_rotation(90)


            save_plot_clf(base_path)

    # ----------------------------------------------------#
    # ----------------------------------------------------#
    # ----------------------------------------------------#

    if name == "variants_state_size":
        t = df
        all_hues = t['protocol'].unique()
        all_hues = sorted(all_hues, key=lambda x: x[-1])
   
        for metric in ["time", "buffer", "downtime"]:
            base_path = "{}/{}-{}".format(
                plot_dir, name, metric
            )
            print("saving to {}".format(base_path))

            ax = sns.lineplot(
                data=t, 
                x='state_size', 
                y=metric, 
                hue='protocol', 
                style="protocol",
                estimator=np.mean,
                hue_order=all_hues,
            )

            ax.set_xlabel("State Transfer Time (ms)")
            ax.set_ylabel(get_ylabel(metric))

            def format_func(value, tick_number):
                return str(int(value*4))

            ax.xaxis.set_major_formatter(plt.FuncFormatter(format_func))


            save_plot_clf(base_path)

    # ----------------------------------------------------#
    # ----------------------------------------------------#
    # ----------------------------------------------------#


    if name == "preliminary":
        for l in [0.85, 0.9, 0.95, 1]:
            tdf = df[df['csrc_load'] == l]
            for metric in ["time", "buffer", "downtime"]:
                ax = sns.lineplot(
                    data=tdf, 
                    x='cdst_load', 
                    y=metric, 
                    hue='protocol', 
                    markers=True,
                    dashes=False
                )

                plt.savefig('{}/{}-{}-load-{}.png'.format(plot_dir, name, metric, l))
                plt.clf()

    if name == "categorical":
        for metric in ["time", "buffer", "downtime"]:
            ax = sns.barplot(
                data=df, 
                x='load', 
                y=metric, 
                hue='protocol', 
                estimator=np.mean,
                errwidth=0
            )

            fmt = '%.3f' if metric == 'time' else '%.1f'
            ax.bar_label(ax.containers[0], fmt=fmt)
            ax.bar_label(ax.containers[1], fmt=fmt)
            name = results_dir.split("/")[-1]
            plt.savefig('{}/{}-{}.png'.format(plot_dir, name, metric))
            plt.clf()


