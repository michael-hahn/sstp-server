import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import csv


def cpu_chart(labels, cpu, cpu_splice, experiment, outfile):
    """
    Plot SSTP server CPU utilization only.
    :param labels: a list of numbers of clients in the experiment, e.g., [1, 2, 4, 8, 16, 32]
    :param cpu: CPU utilization corresponds to labels
    :param cpu_splice: same as CPU, but the splice results
    :param experiment: 'UDP' or 'TCP'
    :param outfile: output file path
    """
    x = labels
    fig, ax = plt.subplots()

    cpu = np.array(cpu)
    cpu_s = np.array(cpu_splice)
    ax.plot(x, cpu_s, color=mcolors.CSS4_COLORS['darkgreen'], marker='^',
            label='Splice')
    ax.plot(x, cpu, color=mcolors.CSS4_COLORS['darkblue'], marker='x', label='Baseline')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylim(0, 1)
    ax.set_xlabel('# of Concurrent iPerf Clients')
    ax.set_ylabel('SSTP Server CPU Utilization (%)')
    # ax.set_title('iPerf {} CPU Utilization'.format(experiment.upper()))
    ax.set_xticks(x)
    ax.set_xticklabels(labels)

    ax.legend(loc='lower right')

    fig.tight_layout()
    # plt.show()
    plt.savefig(outfile)


def mem_chart(labels, mem, mem_splice, experiment, outfile):
    """
    Plot SSTP server memory usage only.
    :param labels: a list of numbers of clients in the experiment, e.g., [1, 2, 4, 8, 16, 32]
    :param mem: memory usage corresponds to labels
    :param mem_splice: same as mem, but the splice results
    :param experiment: 'UDP' or 'TCP'
    :param outfile: output file path
    """
    x = np.arange(len(labels))  # the label locations
    width = 0.20                # the width of the bars

    fig, ax = plt.subplots()

    # Plot memory data
    mem = np.array(mem)
    mem_s = np.array(mem_splice)
    ax.bar(x - width / 2, mem, width, color=mcolors.CSS4_COLORS['white'], edgecolor=mcolors.CSS4_COLORS['black'], label='Baseline')
    ax.bar(x + width / 2, mem_s, width, color=mcolors.CSS4_COLORS['black'], label='Splice)')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_xlabel('# of Concurrent iPerf Clients')
    ax.set_ylabel('SSTP Server Memory Usage (MB)')
    # ax.set_title('iPerf {} Memory Usage'.format(experiment.upper()))
    ax.set_xticks(x)
    ax.set_xticklabels(labels)

    # ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), fancybox=True, ncol=2)
    ax.legend()

    fig.tight_layout()
    # plt.show()
    plt.savefig(outfile)


def parse_cpumem_stats(fp, skip=5):
    """
    Parse CPU and memory statistics.
    :param fp: the file path that stores the statistics
    :param skip: the number of first several lines to skip (system is not yet steady, default to 10)
    :returns a dictionary containing results for each type of request
    """
    cpu = []
    mem = []
    counter = 0
    with open(fp) as csvfile:
        csvreader = csv.DictReader(csvfile, fieldnames=['time', 'pid', 'virt', 'res', '%cpu', '%mem'])
        for row in csvreader:
            if counter < skip:
                counter += 1
            else:
                cpu.append(float(row['%cpu'])/100)
                mem.append(float(row['res'])/1000)
    return {'%cpu': sum(cpu) / len(cpu),
            'mem': sum(mem) / len(mem)}


def parse_all_data(clients, experiment, outfile):
    """
    Parses all data from running the iPerf3 experiment.
    :param clients: a list of numbers of clients from small to large, e.g., [1,2,4,8]
    :param experiment: 'tcp' or 'udp'
    :param outfile: output file path
    """
    mem = []
    mem_splice = []
    cpu = []
    cpu_splice = []
    for client in clients:
        fp = "./data/data-{}/iperf-{}-{}/{}_cpumem.json".format(experiment, client, experiment, client)
        fp_splice = "./data/data-{}/iperf-{}-{}-splice/{}_cpumem.json".format(experiment, client, experiment, client)
        r = parse_cpumem_stats(fp)
        r_s = parse_cpumem_stats(fp_splice)

        mem.append(r['mem'])
        cpu.append(r['%cpu'])
        mem_splice.append(r_s['mem'])
        cpu_splice.append(r_s['%cpu'])
    
    cpu_chart(clients, cpu, cpu_splice, experiment, "{}-cpu".format(outfile))
    mem_chart(clients, mem, mem_splice, experiment, "{}-mem".format(outfile))


if __name__ == '__main__':
    parse_all_data([1, 2, 4, 6, 8, 10], 'tcp','tcp')
    parse_all_data([1, 2, 4, 6, 8], 'udp', 'udp')

