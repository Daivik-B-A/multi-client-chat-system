from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.tcp import tcp

# Import POX's built-in working L2 switch
from pox.forwarding.l2_learning import LearningSwitch

log = core.getLogger()

class MonitoredChatController(object):
    def __init__(self):
        core.openflow.addListeners(self)
        log.info("=== SDN Chat Priority Monitoring Active ===")

    def _handle_ConnectionUp(self, event):
        # Attach standard L2 forwarding logic to the switch
        LearningSwitch(event.connection, False)
        log.info(f"OpenFlow Switch {event.dpid} connected with L2 Learning Enabled.")

    def _handle_PacketIn(self, event):
        packet = event.parsed
        if not packet.parsed:
            return

        # Intercept and log TCP Chat Server traffic on Port 6666
        ipv4_pkt = packet.find(ipv4)
        if ipv4_pkt:
            tcp_pkt = packet.find(tcp)
            if tcp_pkt and (tcp_pkt.dstport == 6666 or tcp_pkt.srcport == 6666):
                log.info(f"[SDN CHAT TRAFFIC DETECTED] Host {ipv4_pkt.srcip} -> Host {ipv4_pkt.dstip} on Port 6666")

def launch():
    core.registerNew(MonitoredChatController)
