The mininet switches need a POX controller to work. 

1. Clone the POX controller:

`git clone -b eel https://github.com/noxrepo/pox.git`

2. In a separate terminal (tmux/screen/etc.), cd into the `pox` directory and: 

`./pox.py pox.forwarding.l2_learning`

This will start the controller, which will be listening on port 6633 by default. Let the controller run in the background and return to the simulator directory. 

3. To run the experiments, python2 and sudo access are required:

`sudo python2 simulator.py 0 30 default`

Which will run the migration with the default settings 30 times. The simulator will set up the topology, establish the connectivity between nodes, sets up the background traffic generators, and will finally run the migration. 

4. The output will be available in the `results` directory for each setting in which the experiments was conducted. 

```
└── results
    └── csrc_load:1+protocol:ERC+...
        └── ERC.res
```

The `res` files will be generate for each protocol. Each line in the output will have the following format: 

`[migration_time] [buffer_size] [downtime] [protocol_start] [phase_2_start] [phase_3_start] [protocol_end]`

5. To run all experiments, run the file `run_all_exp.sh`, which will run the following experiments: 

* heatmap_src_dst_load
* heatmap_src_dst_delay
* power_saving
* load_balancing
* control_latency_reduction
* state_size

6. To plot the results, run the `plot_results2.py` with python3. The plots can be found in the `plots` directory.
