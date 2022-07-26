BUFFER_AT_FINISH = "./logs/buffer_finish.txt"
BUFFER_AT_START = "./logs/buffer_start.txt"
START_TIME = "./logs/start_time.txt"
FINISH_TIME = "./logs/finish_time.txt"

PHASE_FINISH = [
    "./logs/phase_1_finish.txt",
    "./logs/phase_2_finish.txt",
    "./logs/phase_3_finish.txt",
    "./logs/phase_4_finish.txt"
]



DUMP_FILE = "./logs/tcpdump.dump"
DUMP_ERR = "./logs/tcpdump.err"
TASKSET_OUTPUT_PATH = './logs/taskset.out'

LOGS_DIR = 'logs'
HOST_LOGS_DIR = 'logs/hosts'
TRAFFIC_RECV_LOGS_DIR = 'logs/iperf/server'
TRAFFIC_SEND_SCRIPT_DIR = 'logs/iperf/sender/scripts'
TRAFFIC_SEND_LOGS_DIR = 'logs/iperf/sender/logs'
TIME_PATTERN = '%H:%M:%S.%f'

SWITCH_BASE_PORT_NO = 2 
BASE_PACKET_RATE = 1000
PACKET_SIZE = 250
TC_RATE_LIMIT = "50mbps"
TC_BURST_SIZE = "50m"
TC_NETEM_DELAY_CONT = 1
TC_NETEM_DELAY_SW = 1
TC_NETEM_LIMIT = "10000"
FULL_CONNECTION_COUNT = 200
CORE_COUNT_FOR_TRAFFIC = 20
ITG_BATCH_SIZE = FULL_CONNECTION_COUNT / CORE_COUNT_FOR_TRAFFIC

ITG_SEND_TIME = 200*1000  # duration of sending in ms


CONNECTION_DONE_PATH = {
    "c-src": './logs/connection-c-src-done',
    "c-dst": './logs/connection-c-dst-done',
    "mig-switch": './logs/connection-mig-switch-done',
}
OK_TO_INITIATE_PATH = "./logs/ok-to-initiate"

CORES = { 
           'ITGRecv':
                {
                    'h5': [47],
                    'h4': [46],
                    'h3': [45],
                },
            'ITGSend':
                {
                    'h2': range(0,20), #"15-42",
                    'h1': range(20,40), #"1-14",
                    'h3': [40],                   
                },
            'TCPDump': 42
        }
