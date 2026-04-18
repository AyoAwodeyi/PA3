from mininet.net import Mininet 
from mininet.cli import CLI
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel

def build_topology():
    setLogLevel('info')
    net = Mininet(link=TCLink)

    # Hosts - LAN 1
    h1 = net.addHost('h1', ip='10.0.0.1/24', defaultRoute='via 10.0.0.254')
    h2 = net.addHost('h2', ip='10.0.0.2/24', defaultRoute='via 10.0.0.254')

    # Hosts - LAN 2
    h3 = net.addHost('h3', ip='10.0.1.1/24', defaultRoute='via 10.0.1.254')
    h4 = net.addHost('h4', ip='10.0.1.2/24', defaultRoute='via 10.0.1.254')

    # Switches
    s1 = net.addSwitch('s1', cls=OVSSwitch, failMode='standalone')
    s2 = net.addSwitch('s2', cls=OVSSwitch, failMode='standalone')

    # Routers
    r1 = net.addHost('r1', ip='')
    r2 = net.addHost('r2', ip='')
    r3 = net.addHost('r3', ip='')
    r4 = net.addHost('r4', ip='')

    # Link specs
    LAN  = dict(bw=1000, delay='1ms')
    CORE = dict(bw=100,  delay='1ms')

    # LAN 1 links
    net.addLink(h1, s1, **LAN)
    net.addLink(h2, s1, **LAN)
    net.addLink(s1, r1, **LAN)

    # LAN 2 links
    net.addLink(h3, s2, **LAN)
    net.addLink(h4, s2, **LAN)
    net.addLink(s2, r4, **LAN)

    # Core diamond links
    net.addLink(r1, r2, **CORE)
    net.addLink(r1, r3, **CORE)
    net.addLink(r2, r4, **CORE)
    net.addLink(r3, r4, **CORE)

    net.start()

    # Router interface IPs
    r1.cmd('ifconfig r1-eth0 10.0.0.254  netmask 255.255.255.0')
    r1.cmd('ifconfig r1-eth1 10.0.12.1   netmask 255.255.255.252')
    r1.cmd('ifconfig r1-eth2 10.0.13.1   netmask 255.255.255.252')

    r2.cmd('ifconfig r2-eth0 10.0.12.2   netmask 255.255.255.252')
    r2.cmd('ifconfig r2-eth1 10.0.24.1   netmask 255.255.255.252')

    r3.cmd('ifconfig r3-eth0 10.0.13.2   netmask 255.255.255.252')
    r3.cmd('ifconfig r3-eth1 10.0.34.1   netmask 255.255.255.252')

    r4.cmd('ifconfig r4-eth0 10.0.1.254  netmask 255.255.255.0')
    r4.cmd('ifconfig r4-eth1 10.0.24.2   netmask 255.255.255.252')
    r4.cmd('ifconfig r4-eth2 10.0.34.2   netmask 255.255.255.252')

    # Enable IP forwarding on routers
    for r in [r1, r2, rS3, r4]:
        r.cmd('sysctl -w net.ipv4.ip_forward=1')

    CLI(net)
    net.stop()

if __name__ == '__main__':
    build_topology()
