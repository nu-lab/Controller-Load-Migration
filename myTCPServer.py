import socket
import subprocess
import thread
import os
import sys
import pickle
import time
from datetime import datetime
import traceback

from migration_protocol_handler import get_protocol_messages, get_protocols_first_message
import constants as cons

all_sockets = {}
m_role = None
message_len = cons.PACKET_SIZE
RTT = 0

def print_and_flush(s):
    print(s)
    sys.stdout.flush()
    sys.stderr.flush()

def connect(ips, ports, role):
    global all_sockets
    for dst_name, dst_ip in ips.items():
        if dst_name == role:
            continue
        else:
            dst_port = ports[dst_name]
            print_and_flush("[{}] I am going to connect to {}:{}".format(datetime.now().time(), get_name(dst_ip), dst_port))
            sock = socket.socket()
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.connect((dst_ip, dst_port))
            print_and_flush("[{}] I have connected to {}".format(datetime.now().time(), get_name(dst_ip)))
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            all_sockets[dst_ip] = sock
    return


def record_time(file_name):
    with open(file_name, 'wb') as f:
        f.write(str(datetime.now().time()))
        f.flush()


def initiate(protocol, role, ips):
    src, dst, msg_ = get_protocols_first_message(protocol)

    if src == role:
        start_time = datetime.now()
        msg = msg_ + '-' + '0'*(message_len - len(msg_) - 1)
        all_sockets[ips[dst]].sendall(msg)
        print("[{}] [SENT] {} to {}".format(start_time.time(), msg_, dst))
        record_time(cons.START_TIME)


def notify_connection_done():
    with open(cons.CONNECTION_DONE_PATH[m_role], 'wb') as f:
        f.write(str(datetime.now().time()))
        f.flush()


def wait_for_ok_to_initiate():
    while not os.path.exists(cons.OK_TO_INITIATE_PATH):
        time.sleep(0.1)
    return

def get_name(addr):
    for name, ip in ips.items():
        if addr == ip:
            return name
    return "unknown entity ({})".format(addr)



def on_new_client(clientsocket, addr, role, protocol, state_size):
    global all_sockets
    client = get_name(addr[0])
    print_and_flush("[{}] {} has connected to me".format(datetime.now().time(), client))
    protocol_msgs = get_protocol_messages(protocol, role)

    # This string will act as the message buffer. Characters read
    # from the socket will be added to the end of the buffer. When 
    # 500 bytes have been accumulated in the buffer, it will be 
    # taken out of the buffer and processed. This will continue
    # as long as messages can be read from the buffer. 
    message_buffer = ""

    try:   
        while True: 
            activator = clientsocket.recv(4096)
            # print_and_flush("[{}] activator: {}".format(datetime.now().time(), activator))

            message_buffer = message_buffer + activator

            while len(message_buffer) >= message_len: 
                current_message = message_buffer[:message_len]
                message_buffer = message_buffer[message_len:]
                command = current_message.split("-")[0]                    
                print_and_flush("[{}] [RECV] {} from {}".format(datetime.now().time(), command, client))

                if command in protocol_msgs:
                    for msg_ in protocol_msgs[command]:
                        dst = msg_[0]
                        msg = msg_[1]

                        if msg.startswith("phase_finish_"):
                            phase = int(msg.split("_")[-1])
                            print_and_flush("[{}] [PHAS] phase {} finished".format(datetime.now().time(), phase))
                            record_time(cons.PHASE_FINISH[phase-1])
                            continue

                        if msg.startswith("stop_buffer"):
                            print_and_flush("[{}] [BUFF] finish".format(datetime.now().time()))
                            record_time(cons.BUFFER_AT_FINISH)
                            continue
                            
                        elif msg.startswith("start_buffer"):
                            print_and_flush("[{}] [BUFF] start".format(datetime.now().time()))
                            record_time(cons.BUFFER_AT_START)
                            continue

                        elif msg.startswith("finish_protocol"):
                            print_and_flush("[{}] [FINISH] {}".format(datetime.now().time(), protocol))
                            record_time(cons.FINISH_TIME)
                            clientsocket.close()
                            exit()

                        send_count = 1
                        if msg == "local_state":
                            send_count = state_size
                        msg += '-' + '0'*(message_len - len(msg) - 1)
                        filler_message = "filler-" + "0" * (message_len - 7)

                        ip = ips[dst]
                        sock = all_sockets[ip]

                        for i in range(send_count):
                            if i == send_count - 1: 
                                ret = sock.send(msg)
                            else: 
                                ret = sock.send(filler_message)
                                time.sleep(float(RTT) / 1000)
                                    
                            print_and_flush("[{}] [SEND] {} to {}".format(datetime.now().time(), msg_[1], dst))
                                   
    except Exception as e: 
        traceback.print_exc()
        print_and_flush(e)

    clientsocket.close()


def start_listening(protocol, role, ips, ports, state_size):
    global all_sockets
    # TCP_IP = "127.0.0.1"
    TCP_IP = ips[role]
    TCP_PORT = ports[role]

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((TCP_IP, TCP_PORT))
    print("[{}] started listening on: {}".format(datetime.now().time(), sock.getsockname()))
    sock.listen(10)
    sys.stdout.flush()
    sys.stderr.flush()

    while True:
        print("[{}] I'm in the accept loop".format(datetime.now().time()))
        c, addr = sock.accept()  # Establish connection with client.
        thread.start_new_thread(on_new_client, (c, addr, role, protocol, state_size,))
    sock.close()


if __name__ == "__main__":
    try:
        global m_role

        role = sys.argv[1]
        protocol = sys.argv[2]
        state_size = int(sys.argv[3])
        m_role = role
        ips_pickled = sys.argv[4]
        ips = pickle.load(open(ips_pickled, "rb"))
        ports_pickled = sys.argv[5]
        ports = pickle.load(open(ports_pickled, "rb"))
        RTT = int(sys.argv[6])

        sys.stdout = open(str("{}/{}.serv.out".format(cons.HOST_LOGS_DIR, role)), "w")
        sys.stderr = open(str("{}/{}.serv.err".format(cons.HOST_LOGS_DIR, role)), "w")

        thread.start_new_thread(start_listening,
                                (protocol, role, ips, ports, state_size,))

        time.sleep(1)  # let other servers to spawn
        connect(ips, ports, role)

        print_and_flush("[{}] going to wait for all the sockets to join".format(datetime.now().time()))
        time.sleep(0.5)
        global all_sockets
        while len(all_sockets) < 2:
            time.sleep(0.01)
            print("[{}] still waiting...".format(datetime.now().time()))

        print_and_flush("[{}] All entities connected! Ready to run the protocol".format(datetime.now().time()))
        print_and_flush("[{}] I will notify the simulator to start the traffic generator.".format(datetime.now().time()))
        
        notify_connection_done()
        wait_for_ok_to_initiate()
        initiate(protocol, role, ips)

        print_and_flush("[{}] Main Thread Finished. Waiting for dummy input.".format(datetime.now().time()))
        c = raw_input()

    except Exception as e:
        print(str(e))
