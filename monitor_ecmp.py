#!/usr/bin/env python3

import sys
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def read_tx_bytes(iface):
    with open('/proc/net/dev', 'r') as f:
        for line in f:
            if iface in line:
                fields = line.split(':')[1].split()
                return int(fields[8])
    return 0

def main():
    interval = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    duration = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0

    eth1_start = read_tx_bytes('r1-eth1')
    eth2_start = read_tx_bytes('r1-eth2')

    times = []
    eth1_cumulative = []
    eth2_cumulative = []
    eth1_rates = []
    eth2_rates = []

    eth1_prev = eth1_start
    eth2_prev = eth2_start

    print(f"{'Time(s)':<10} {'ETH1 Cum(MB)':<15} {'ETH1 Rate(MB/s)':<18} {'ETH2 Cum(MB)':<15} {'ETH2 Rate(MB/s)':<15}")
    print('-' * 75)

    elapsed = 0.0
    while elapsed < duration:
        time.sleep(interval)
        elapsed += interval

        eth1_now = read_tx_bytes('r1-eth1')
        eth2_now = read_tx_bytes('r1-eth2')

        eth1_cum = (eth1_now - eth1_start) / 1e6
        eth2_cum = (eth2_now - eth2_start) / 1e6
        eth1_rate = (eth1_now - eth1_prev) / 1e6 / interval
        eth2_rate = (eth2_now - eth2_prev) / 1e6 / interval

        times.append(elapsed)
        eth1_cumulative.append(eth1_cum)
        eth2_cumulative.append(eth2_cum)
        eth1_rates.append(eth1_rate)
        eth2_rates.append(eth2_rate)

        print(f"{elapsed:<10.1f} {eth1_cum:<15.2f} {eth1_rate:<18.2f} {eth2_cum:<15.2f} {eth2_rate:<15.2f}")

        eth1_prev = eth1_now
        eth2_prev = eth2_now

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    ax1.plot(times, eth1_cumulative, label='r1-eth1')
    ax1.plot(times, eth2_cumulative, label='r1-eth2')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Cumulative TX (MB)')
    ax1.set_title('Cumulative TX over Time')
    ax1.legend()
    ax1.grid(True)

    ax2.plot(times, eth1_rates, label='r1-eth1')
    ax2.plot(times, eth2_rates, label='r1-eth2')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('TX Rate (MB/s)')
    ax2.set_title('Instantaneous TX Rate')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig('/tmp/r1_ecmp_traffic.png')
    print("\nPlot saved to /tmp/r1_ecmp_traffic.png")

if __name__ == '__main__':
    main()
