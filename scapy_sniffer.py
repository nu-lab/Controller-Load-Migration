from scapy.all import *
import constants as cons
import time

sys.stdout = open(str(cons.DUMP_FILE), "w")
sys.stderr = open(str(cons.DUMP_ERR), "w")

counter = 0
# conf.iface = cons.CONF_IFACE
def handle_packet(packet):
    global counter
    counter = counter + 1
    print("{},{}".format(time.time(), counter))
    sys.stdout.flush()
    
sniff(filter="src host 10.0.0.2 and dst host 10.0.0.5 and dst port 2223", prn=handle_packet, store=False) #TODO: make this dynamic (i.e., addresses and port)
