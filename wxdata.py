#!/usr/bin/env python3

import json
import sys
import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def plot_jsonl_data(datafile):
    datasets = {}
    # keys for datasets are measured quantities, like 'temperature'.
    # values are [[list of datetimes], [list of values]]

    with open(datafile) as fp:
        for line in fp:
            report = json.loads(line)
            # report is a dict whose keys include 'time'
            # plus measured quantities like 'temperature'.
            try:
                report['time']
                report_time = datetime.datetime.strptime(report['time'][:19],
                                                         '%Y-%m-%dT%H:%M:%S')
            except KeyError:
                print("Line doesn't have 'time':", line)
                continue
            for key in report:
                if key == 'time':
                    continue
                if key in datasets:
                    datasets[key][0].append(report_time)
                    datasets[key][1].append(float(report[key]))
                else:
                    datasets[key] = [ [ report_time ], [ float(report[key]) ] ]

    fig, ax = plt.subplots()
    key = 'temperature'
    ax.plot(datasets[key][0], datasets[key][1])

    # Trim excessive whitespace
    plt.tight_layout(pad=2.0, w_pad=10.0, h_pad=3.0)

    xformatter = mdates.DateFormatter('%H:%M')
    # xlocator = mdates.MinuteLocator(interval = 15)
    xlocator = mdates.MinuteLocator(byminute=[0,30], interval = 1)

    # Set xtick labels to appear every 15 minutes
    ax.xaxis.set_major_locator(xlocator)

    # Format xtick labels as HH:MM
    ax.xaxis.set_major_formatter(xformatter)

    # Exit on key q
    plt.figure(1).canvas.mpl_connect('key_press_event',
                                     lambda e:
                                     sys.exit(0) if e.key == 'ctrl+q'
                                                 else None)

    plt.show()

if __name__ == '__main__':
    plot_jsonl_data(sys.argv[1])

