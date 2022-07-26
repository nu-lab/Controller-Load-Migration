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


class MyTopo(Topo):
    """
        h4---s3---s1---s2---h5
                 /|\
                / | \
               / s4  \
              /   |   \
             /    |    \
           h1  mig-sw   h2
           /             \
    n1 tcp cons.       n2 tcp cons.   (these TCP connections are to simulate the load and are established via iperf)

    h1 and h2 are simulating the connected switches to h4 and h5, respectively.
    Their corresponding traffic is passing through s1.
    The order that we assign the switch ports will give cons.SWITCH_BASE_PORT_NO to h3.
    This way, in order to count the number of buffered messages, we only need to measure the number of
    packets passed through the corresponding port on the connection between h3 and s1 between two
    time events: start_buffer and finish (these are two specialized messages that we use as our protocol messages).
    The protocol messages are being sent over a separate UDP socket and being received in myServer that we bring 
    up on both the controllers and h3. myServer knows how to deal with different protocol-specific messages. 
    """

    def __init__(self, *args, **params):
        self.host_link_map = {}
        super(MyTopo, self).__init__(*args, **params)

    def build(self):

        s1 = self.addSwitch('s1')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')
        s5 = self.addSwitch('s5')
        

        # adding the simulated switch involved in the migration
        host = self.addHost("h3")
        self.addLink(host, s3)
        
        # adding the source controller
        host = self.addHost("h4")
        self.addLink(host, s4)

        # adding the destination controller
        host = self.addHost("h5")
        self.addLink(host, s5)  
        
        # h1 and h2 are being used for two purposes:
        #   1. Traffic generator toward controllers (simulating the Packet_In messages)
        #   2. Receiver of the traffic from controllers
        host = self.addHost("h1")
        self.addLink(host, s4)

        host = self.addHost("h2")
        self.addLink(host, s5)

        self.addLink(s1, s3)
        self.addLink(s1, s4)
        self.addLink(s1, s5)
