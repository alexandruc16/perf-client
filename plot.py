import argparse
import json
import matplotlib.dates
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime, timedelta
from matplotlib.pyplot import cm


overall_data = dict()


def plot_overall_cdf(data, labels, folder, fig_name=None):
    fig = plt.figure(figsize=[16.0, 8.0])
    ax = fig.add_subplot(111)
    color = cm.rainbow(np.linspace(0, 1, len(data)))

    for i in range(len(data)):
        bws = [float(x / (1024 * 1024)) for x in data[i]]
        x = np.sort(bws)
        y = np.array(range(len(bws))) / float(len(bws))
        ax.plot(x, y, c=color[i], label=labels[i], alpha=(1 - ((1 / len(data)) * i)))

    ax.margins(0.05)
    ax.grid()
    handles, lbls = ax.get_legend_handles_labels()
    ax.legend(handles, lbls)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
    plt.xlabel('Bandwidth (Mbps)')
    plt.ylabel('Probability')
    plt.ticklabel_format(style='plain', useOffset=False)
    #plt.xlim(xmin=min(bws)-0.05*(max(bws)-min(bws))) # TODO
    #plt.ylim(ymin=0)

    fig_name = os.path.join(folder, fig_name + "_cdf.png")

    plt.savefig(fig_name)
    plt.close('all')


def plot_overall_bw_data(data, ticks, labels, folder, fig_name=None):
    if len(data) == 0:
        return

    fig = plt.figure(figsize=[16.0, 8.0])
    ax = fig.add_subplot(111)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
    ax.margins(0.05)
    ax.grid()
    #plt.ylim(ymin=-0.05, ymax=1.05*max(bws)) # TODO
    color = cm.rainbow(np.linspace(0, 1, len(data)))

    for i in range(len(data)):
        bws = [float(x / (1024 * 1024)) for x in data[i]]
        ax.plot(ticks[i], bws, c=color[i], marker='.', linestyle='', label=labels[i], alpha=(1 - ((1 / len(data)) * i)))

    handles, lbls = ax.get_legend_handles_labels()
    ax.legend(handles, lbls)
    plt.xlabel('time (s)')
    plt.ylabel('bandwidth (Mbps)')

    fig_name = os.path.join(folder, fig_name + '.png')

    plt.savefig(fig_name)
    plt.close('all')


def plot_overall(root_folder):
    for instance in overall_data.keys():
        data = []
        labels = []
        ticks = []

        for experiment in overall_data[instance].keys():
            for region in overall_data[instance][experiment].keys():
                data.append(overall_data[instance][experiment][region])
                label = "%s@%s" % (experiment, region)
                labels.append(label)

                if experiment == 'full_speed':
                    ticks.append(range(len(overall_data[instance][experiment][region])))
                elif experiment == '5sec_30sec':
                    ticks.append(range(0, 3 * len(overall_data[instance][experiment][region]), 3))
                elif experiment == '10sec_30sec':
                    ticks.append(range(0, 3 * len(overall_data[instance][experiment][region]), 3))
                elif experiment == '10sec_60sec':
                    ticks.append(range(0, 6 * len(overall_data[instance][experiment][region]), 6))

        plot_overall_bw_data(data, ticks, labels, root_folder, instance)
        plot_overall_cdf(data, labels, root_folder, instance)


def plot_cdf(date, data, folder, fig_name=None):
    bws = [float(x / (1024 * 1024)) for x in data]
    x = np.sort(bws)
    y = np.array(range(len(bws)))/float(len(bws))
    fig = plt.figure(figsize=[16.0, 8.0])
    ax = fig.add_subplot(111)
    ax.plot(x, y)

    if fig_name is None:
        fig_name = os.path.join(folder, date.strftime('%Y-%m-%d') + '_cdf')

    ax.margins(0.05)
    ax.grid()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
    plt.xlabel('Bandwidth (Mbps)')
    plt.ylabel('Probability')
    plt.ticklabel_format(style='plain', useOffset=False)
    plt.xlim(xmin=min(bws)-0.05*(max(bws)-min(bws)))
    #plt.ylim(ymin=0)
    plt.savefig(fig_name)
    plt.close('all')


def plot_bw_data(date, data, folder, fig_name=None, interval=10):
    if len(data) == 0:
        return

    bws = [float(x / (1024*1024)) for x in data]
    tick_dates = []
    tick_dates.append(date)

    for i in range(0, len(bws) - 1):
        date = date + timedelta(seconds=interval)
        tick_dates.append(date)

    fig = plt.figure(figsize=[16.0, 8.0])
    ax = fig.add_subplot(111)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
    ax.margins(0.05)
    ax.grid()
    plt.ylim(ymin=-0.05, ymax=1.05*max(bws))
    ax.plot_date(tick_dates, bws, fmt='b.')
    fig.autofmt_xdate()
    plt.xlabel('timestamp')
    plt.ylabel('bandwidth (Mbps)')

    if fig_name is None:
        fig_name = os.path.join(folder, date.strftime('%Y-%m-%d'))
        ax.xaxis.set_major_locator(matplotlib.dates.HourLocator())
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M"))
    else:
        ax.xaxis.set_major_locator(matplotlib.dates.DayLocator(interval=1))
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d-%m-%Y"))
        ax.xaxis.set_minor_locator(matplotlib.dates.HourLocator(byhour=range(0, 24, 1)))

    plt.savefig(fig_name)
    plt.close('all')


def process_bw_reports(root_folder, delay=10):
    regions = [f for f in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, f))]

    for region in regions:
        region_folder = os.path.join(root_folder, region)
        instances = [i for i in os.listdir(region_folder) if os.path.isdir(os.path.join(region_folder, i))]

        for instance in instances:
            instance_folder = os.path.join(region_folder, instance)
            files = sorted([os.path.join(instance_folder, f) for f in os.listdir(instance_folder) if f.endswith('.json')])
            instance_start = None
            dt = None
            data = []
            data_length = len(data)

            for filename in files:
                with open(filename, 'r') as f:
                    contents = json.loads(f.read())
                    start = datetime.utcfromtimestamp(contents['start']['timestamp']['timesecs'])

                    if dt is None:
                        dt = start

                    if instance_start is None:
                        instance_start = start

                    for interval in contents['intervals']:  # reports every 10 seconds
                        if 'sum' in interval:
                            data.append(interval['sum']['bits_per_second'])
                            start = start + timedelta(seconds=delay)

                            if len(data[data_length:]) > 0 and start.day != dt.day:
                                plot_bw_data(dt, data[data_length:], instance_folder, interval=delay)
                                plot_cdf(dt, data[data_length:], instance_folder)
                                dt = start
                                data_length = len(data)

            if len(data[data_length:]) > 0:
                plot_bw_data(dt, data[data_length:], instance_folder, interval=delay)
                plot_cdf(dt, data[data_length:], instance_folder)

            if instance not in overall_data.keys():
                overall_data[instance] = dict()

            if os.path.basename(root_folder) not in overall_data[instance].keys():
                overall_data[instance][os.path.basename(root_folder)] = dict()

            if region not in overall_data[instance][os.path.basename(root_folder)].keys():
                overall_data[instance][os.path.basename(root_folder)][region] = data

            plot_bw_data(instance_start, data, instance_folder, fig_name=os.path.join(instance_folder, instance+'.png'), interval=delay)  # plot overall instance results
            plot_cdf(instance_start, data, instance_folder, fig_name=os.path.join(instance_folder, instance+'_cdf.png'))


def main():
    parser = argparse.ArgumentParser(description="Generate plots from benchmark "
                                     "results.", epilog = "Example Usage: "
                                     "python plot_reports.py "
                                     "<path-to-results-directory>")

    parser.add_argument("results_directory",
                        action="store",
                        help="Path to directory containing benchmark results.")
                        
    args = parser.parse_args()
    experiment_folders = [os.path.join(args.results_directory, f) for f in os.listdir(args.results_directory) if os.path.isdir(os.path.join(args.results_directory, f))]

    for f in experiment_folders:
        interval = 10
        folder_name = os.path.basename(f)
        if folder_name == 'full_speed':
            interval = 10
        elif folder_name == '5sec_30sec':
            interval = 30
        elif folder_name == '10sec_30sec':
            interval = 30
        elif folder_name == '10sec_60sec':
            interval = 60

        process_bw_reports(f, interval)

    plot_overall(args.results_directory)


if __name__ == "__main__":
    main()

