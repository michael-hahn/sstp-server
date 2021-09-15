import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.ticker as mtick
import numpy as np


def parse_deletion_log(fp):
    r = {'sys_obj_to_delete': 0, 'non_sys_obj_to_delete': 0,
         'total_sys_obj_del_time': 0.0, 'total_non_sys_obj_del_time': 0.0}
    with open(fp) as f:
        for line in f:
            # This line tells us the number of total objects
            # 2021-09-14 22:58:39,590 INFO: [splice] Getting all 35122 heap objects takes: 0.0037771861534565687s
            if "Getting all" in line:
                data = line.strip().split()
                r['num_total_objs'] = int(data[6])
                r['obj_discovery_time'] = float(data[10][:-1]) * 1000 # in msec
            # These lines tell us the time to delete a system object
            # 2021-09-14 22:58:39,590 INFO: [splice] Taking 1.7171958461403847e-05s to delete system object: <_io.FileIO name=16 mode='rb' closefd=True>
            if "Taking" in line and "system object" in line:
                data = line.strip().split()
                r['sys_obj_to_delete'] += 1
                r['total_sys_obj_del_time'] += float(data[5][:-1]) * 1000 # in msec
            # These lines tell us the time to delete a non-system object
            # 2021-09-14 22:58:39,646 INFO: [splice] Taking 2.2239983081817627e-06s to delete non-system object: 192.168.20.1:192.168.20.3
            if "Taking" in line and "non-system object" in line:
                data = line.strip().split()
                r['non_sys_obj_to_delete'] += 1
                r['total_non_sys_obj_del_time'] += float(data[5][:-1]) * 1000 # in msec
    return r


def deletion_data_chart(xticks, xlabel, data, data_label, title, outfile,
                        object_discovery_data=None, system_data=None, non_system_data=None, annotation_data=None):
    """
    Plot the deletion data.
    :param xticks: x-axis data
    :param xlabel: x-axis label
    :param data: data to be plotted (y-axis)
    :param data_label: y-axis label
    :param title: title of the plot
    :param outfile: output file path
    """
    x = xticks
    fig, ax = plt.subplots()

    # Plot data
    d = np.array(data)
    ax.plot(x, d, color=mcolors.CSS4_COLORS['darkorange'], marker='x', label='Overall Deletion Cost')
    if object_discovery_data:
        odd = np.array(object_discovery_data)
        ax.plot(x, odd, color=mcolors.CSS4_COLORS['darkgreen'], marker='o', label='Heap Walk')
        # Add annotation data to show the number of objects discovered in heap walk
        counter = 0
        for i, j in zip(x, odd):
            ax.annotate('{:,}'.format(annotation_data[counter]), xy=(i, j))#, xytext=(10, -5), textcoords='offset points')
            counter += 1

    if system_data:
        sd = np.array(system_data)
        ax.plot(x, sd, color=mcolors.CSS4_COLORS['darkblue'], marker='^', label='Deletion Manager')
    if non_system_data:
        nsd = np.array(non_system_data)
        ax.plot(x, nsd, color=mcolors.CSS4_COLORS['grey'], marker='2', label='Other Objects')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_xlabel(xlabel)
    ax.set_ylabel(data_label)
    # ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(xticks)
    ax.legend()

    fig.tight_layout()
    # plt.show()
    plt.savefig(outfile)


def parse_deletion_data(users, xlabel, ylabel, title, outfile):
    total_time = []
    heap_walk_time = []
    system_time = []
    non_system_time = []
    num_heap_objs = []

    for user in users:
        fp = "./data/data-deletion/sstp-del-{}.log".format(user)
        r = parse_deletion_log(fp)
        total_time.append(r['obj_discovery_time'] + r['total_sys_obj_del_time'] + r['total_non_sys_obj_del_time'])
        heap_walk_time.append(r['obj_discovery_time'])
        system_time.append(r['total_sys_obj_del_time'])
        non_system_time.append(r['total_non_sys_obj_del_time'])
        num_heap_objs.append(r['num_total_objs'])
    deletion_data_chart(users, xlabel, total_time, ylabel, title, outfile, heap_walk_time, system_time, non_system_time, num_heap_objs)


if __name__ == '__main__':
    parse_deletion_data([1, 2, 4, 8, 16, 32], "# of Users", "Time (msec)", "SSTP Deletion Performance", "sstp")

