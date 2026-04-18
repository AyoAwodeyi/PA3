#!/usr/bin/env python3

import os
import time
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import Node, OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel


class FRR(Node):
    def __init__(self, name, **params):
        super(FRR, self).__init__(name, **params)
        self.run_dir  = f'/tmp/{name}-run'
        self.conf_dir = f'/tmp/{name}-conf'

    def start_frr(self, networks):
        self.cmd('sysctl -w net.ipv4.ip_forward=1')
        self.cmd('sysctl -w net.ipv4.fib_multipath_hash_policy=1')
        self.cmd(f'rm -rf {self.run_dir}')
        self.cmd(f'mkdir -p {self.run_dir}')
        self.cmd(f'chown frr:frr {self.run_dir}')
        self.cmd(f'chmod 775 {self.run_dir}')
        os.makedirs(self.conf_dir, exist_ok=True)
        conf_file = f'{self.conf_dir}/frr.conf'
        net_config = "\n".join([f" network {net} area 0" for net in networks])
        config = (
            "hostname {name}\n"
            "password zebra\n"
            "log stdout\n"
            "!\n"
            "router ospf\n"
            " ospf router-id {id}\n"
            "{networks}\n"
            "!\n"
        ).format(
            name=self.name,
            id=self.params.get('router_id', '1.1.1.1'),
            networks=net_config
        )
        with open(conf_file, 'w') as f:
            f.write(config)
        self.cmd(f'chown -R frr:frr {self.conf_dir}')
        self.cmd(f'/usr/lib/frr/zebra -d -f {conf_file} -u frr -g frr '
                 f'-z {self.run_dir}/zserv.api --vty_socket {self.run_dir} '
                 f'-i {self.run_dir}/zebra.pid')
        self.cmd(f'/usr/lib/frr/ospfd -d -f {conf_file} -u frr -g frr '
                 f'-z {self.run_dir}/zserv.api --vty_socket {self.run_dir} '
                 f'-i {self.run_dir}/ospfd.pid')
        self.wait_for_sockets()

    def wait_for_sockets(self):
        print(f"Waiting for FRR sockets on {self.name}...")
        for _ in range(10):
            result = self.cmd(f'ls {self.run_dir}/zebra.vty 2>/dev/null')
            if 'zebra.vty' in result:
                self.cmd(f'chmod 666 {self.run_dir}/*.vty')
                self.cmd(f'chmod 666 {self.run_dir}/zserv.api')
                return
            time.sleep(0.5)
        print(f"Warning: FRR sockets did not appear for {self.name}.")

    def terminate(self):
        self.cmd(f'kill -9 $(cat {self.run_dir}/ospfd.pid) 2>/dev/null')
        self.cmd(f'kill -9 $(cat {self.run_dir}/zebra.pid) 2>/dev/null')
        self.cmd(f'rm -rf {self.run_dir}')
        self.cmd(f'rm -rf {self.conf_dir}')
        super(FRR, self).terminate()


def build_topology():
    setLogLevel('info')
    net = Mininet(link=TCLink)

    h1 = net.addHost('h1', ip='10.0.0.1/24', defaultRoute='via 10.0.0.254')
    h2 = net.addHost('h2', ip='10.0.0.2/24', defaultRoute='via 10.0.0.254')
    h3 = net.addHost('h3', ip='10.0.1.1/24', defaultRoute='via 10.0.1.254')
    h4 = net.addHost('h4', ip='10.0.1.2/24', defaultRoute='via 10.0.1.254')

    s1 = net.addSwitch('s1', cls=OVSSwitch, failMode='standalone')
    s2 = net.addSwitch('s2', cls=OVSSwitch, failMode='standalone')

    r1 = net.addHost('r1', cls=FRR, ip='', router_id='1.1.1.1')
    r2 = net.addHost('r2', cls=FRR, ip='', router_id='2.2.2.2')
    r3 = net.addHost('r3', cls=FRR, ip='', router_id='3.3.3.3')
    r4 = net.addHost('r4', cls=FRR, ip='', router_id='4.4.4.4')

    LAN  = dict(bw=1000, delay='1ms')
    CORE = dict(bw=100,  delay='1ms')

    net.addLink(h1, s1, **LAN)
    net.addLink(h2, s1, **LAN)
    net.addLink(s1, r1, **LAN)

    net.addLink(h3, s2, **LAN)
    net.addLink(h4, s2, **LAN)
    net.addLink(s2, r4, **LAN)

    net.addLink(r1, r2, **CORE)
    net.addLink(r1, r3, **CORE)
    net.addLink(r2, r4, **CORE)
    net.addLink(r3, r4, **CORE)

    net.start()

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

    r1.start_frr(['10.0.0.0/24', '10.0.12.0/30', '10.0.13.0/30'])
    r2.start_frr(['10.0.12.0/30', '10.0.24.0/30'])
    r3.start_frr(['10.0.13.0/30', '10.0.34.0/30'])
    r4.start_frr(['10.0.1.0/24', '10.0.24.0/30', '10.0.34.0/30'])

    print("\n*** Waiting 40s for OSPF to converge... ***\n")
    time.sleep(40)

    CLI(net)
    net.stop()


if __name__ == '__main__':
    build_topology()
