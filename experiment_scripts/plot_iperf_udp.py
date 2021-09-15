import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


def parse_udp_server_data(fp):
    with open(fp) as f:
        for line in f:
            # We want lines that look like this (we should have at least 60 of them):
            # [  6]   0.00-60.00  sec  4.75 GBytes   680 Mbits/sec  0.011 ms  135634/3656010 (3.7%)  receiver
            if "[  6]" in line and "receiver" in line:
                data = line.strip().split()
                mbits_per_sec = float(data[6])
                return mbits_per_sec


def bandwidth_fig(clients, bandwidths, bandwidths_with_splice, outfile):
    """
    Plot bandwidth results as reported by iPerf.
    :param clients: a list of numbers of clients in the experiment, e.g., [1, 2, 4, 8, 16, 32]
    :param bandwidths: a list of bandwidth results corresponding to the clients
    :param bandwidths_with_splice: same as bandwidths, but the splice results
    :param outfile: output file path
    """
    # x = np.arange(len(clients))  # the label locations
    x = clients

    fig, ax = plt.subplots()

    # Plot data
    d = np.array(bandwidths)
    d_s = np.array(bandwidths_with_splice)
    ax.plot(x, d, color=mcolors.CSS4_COLORS['darkblue'], marker='x', label='Baseline')
    ax.plot(x, d_s, color=mcolors.CSS4_COLORS['darkgreen'], marker='^',
            label='Splice')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_xlabel('# of Concurrent iPerf Clients')
    ax.set_ylabel('Bandwidth (Mbs/sec)')
    # ax.set_title('iPerf UDP Bandwidth Performance')
    ax.set_xticks(x)
    ax.set_xticklabels(clients)
    ax.legend()

    fig.tight_layout()
    # plt.show()
    plt.savefig(outfile)


def parse_workload_data(clients, outfile):
    """
    Parses all UDP data from the server side from running the workload.
    :param clients: a list of numbers of clients from small to large, e.g., [1,2,4,8]
    :param outfile: output file path
    """
    bandwidths = []
    bandwidths_with_splice = []
    # The address of the iPerf client is part of the name of the statistics file
    # The client address should start from 172.18.0.3 and increase sequentially.
    client_ip_base = '172.18.0.'
    client_ip_suffix = 3
    for client in clients:
        bandwidth_l = 0.0
        bandwidth_l_s = 0.0
        for i in range(client):
            fp = "./data/data-udp/iperf-{}-udp/{}{}-{}-udp.json".format(client, client_ip_base, client_ip_suffix + i, client)
            fp_splice = "./data/data-udp/iperf-{}-udp-splice/{}{}-{}-splice-udp.json".format(client, client_ip_base, client_ip_suffix + i, client)
            r = parse_udp_server_data(fp)
            r_s = parse_udp_server_data(fp_splice)

            if r:
                bandwidth_l += r
            if r_s:
                bandwidth_l_s += r_s

        bandwidths.append(bandwidth_l)
        bandwidths_with_splice.append(bandwidth_l_s)

    bandwidth_fig(clients, bandwidths, bandwidths_with_splice, outfile)

if __name__ == '__main__':
    parse_workload_data([1, 2, 4, 6, 8], 'udp-bandwidth')
