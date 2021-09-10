import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


def latency_fig(clients, data, data_with_splice, outfile):
    """
    Plot latency results as reported by Puppeteer.
    :param clients: a list of numbers of clients in the experiment, e.g., [1, 2, 4, 8, 16, 32]
    :param data: a list of results corresponding to the clients
    :param data_with_splice: same as data, but the splice results
    :param outfile: output file path
    """
    # x = np.arange(len(clients))  # the label locations
    x = clients

    fig, ax = plt.subplots()

    # Plot data
    d = np.array(data)
    d_s = np.array(data_with_splice)
    ax.plot(x, d, color=mcolors.CSS4_COLORS['darkblue'], marker='x', label='w/o Splice')
    ax.plot(x, d_s, color=mcolors.CSS4_COLORS['darkgreen'], marker='^',
            label='w/ Splice')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_xlabel('# of Concurrent Puppeteer Clients')
    ax.set_ylabel('Latency (msecs)')
    ax.set_title('Puppeteer Performance')
    ax.set_xticks(x)
    ax.set_xticklabels(clients)
    ax.legend()

    fig.tight_layout()
    # plt.show()
    plt.savefig(outfile)


def parse_puppeteer_stats(fp):
    """
    Parse Puppeteer statistics as captured by Puppeteer.
    :param fp: the file path that stores the Puppeteer statistics
    :returns a dictionary containing results
    """
    d = {}
    with open(fp) as f:
        client_data = json.load(f)
        start = client_data["navigationStart"]
        end = client_data['loadEventEnd']
        d['latency'] = float(end - start)
    return d


def parse_workload_data(clients, outfile):
    """
    Parses all Puppeteer data from running the workload.
    :param clients: a list of numbers of clients from small to large, e.g., [1,2,4,8]
    :param outfile: output file path
    """
    latency = []
    latency_with_splice = []
    # The address of the iPerf client is part of the name of the statistics file
    # The client address should start from 172.18.0.3 and increase sequentially.
    client_ip_base = '172.18.0.'
    client_ip_suffix = 3
    for client in clients:
        for i in range(client):
            fp = "./data/puppeteer-{}-remote/{}{}-{}-remote.json".format(client, client_ip_base, client_ip_suffix + i, client)
            fp_splice = "./data/puppeteer-{}-remote-splice/{}{}-{}-udp.json".format(client, client_ip_base,
                                                                              client_ip_suffix + i, client)
            r = parse_puppeteer_stats(fp)
            r_s = parse_puppeteer_stats(fp_splice)

    latency_fig(clients, latency, latency_with_splice, outfile)


if __name__ == '__main__':
    pass
