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
    ax.plot(x, d_s, color=mcolors.CSS4_COLORS['darkgreen'], marker='^',
            label='Splice')
    ax.plot(x, d, color=mcolors.CSS4_COLORS['darkblue'], marker='x', label='Baseline')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_xlabel('# of Concurrent Puppeteer Clients')
    ax.set_ylabel('Average Page Load Time (msecs)')
    ax.set_ylim(bottom=0)
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


def parse_puppeteer_multi_stats(fp):
    """
    When running puppeteer to fetch multiple pages, the stats that
    we recorded are no longer in JSON. We just have to parse them
    normally, one line at a time
    """
    latencies = []
    with open(fp) as f:
        start = 0
        end = 0
        for line in f:
            if "navigationStart" in line:
                start = int(line.strip().split()[1][:-1])
            elif "loadEventEnd" in line and "unloadEventEnd" not in line:
                end = int(line.strip().split()[1][:-1])
                latencies.append(end - start)
    # print(latencies)
    return {'latency': sum(latencies)/len(latencies)}


def parse_workload_data(clients, outfile):
    """
    Parses all Puppeteer data from running the workload.
    :param clients: a list of numbers of clients from small to large, e.g., [1,2,4,8]
    :param outfile: output file path
    """
    latency = []
    latency_with_splice = []
    for client in clients:
        l = []
        l_s = []
        for i in range(1, client+1):
            fp = "./data/puppeteer-{}-remote/{}.json".format(client, i)
            fp_splice = "./data/puppeteer-{}-remote-splice/{}.json".format(client, i)
            r = parse_puppeteer_multi_stats(fp)
            r_s = parse_puppeteer_multi_stats(fp_splice)
            
            l.append(r['latency'])
            l_s.append(r_s['latency'])
       
        latency.append(sum(l)/len(l))
        latency_with_splice.append(sum(l_s)/len(l_s))

    latency_fig(clients, latency, latency_with_splice, outfile)


if __name__ == '__main__':
    parse_workload_data([1, 2, 3, 4, 5, 6], 'puppeteer-page-load')
