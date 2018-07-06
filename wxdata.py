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

    # Figure out layout. If 2 or fewer quantities, lay out vertically;
    # otherwise use 2 columns.
    nplots = len(datasets)
    if nplots <= 2:
        nrows = nplots
        ncols = 1
    else:
        ncols = 2
        nrows = int(len(datasets) / 2 + .5)    # divide by 2 and round up

    # Simple time formatter
    xformatter = mdates.DateFormatter('%H:%M')
    # Set xtick labels every 15 minutes
    xlocator = mdates.MinuteLocator(byminute=[0,30], interval = 1)

    # fig, ax = plt.subplots()
    fig = plt.figure()
    for i, key in enumerate(datasets):
        # row = i // 2
        # col = i % 2
        ax = fig.add_subplot(nrows, ncols, i+1)
        ax.plot(datasets[key][0], datasets[key][1])

        ax.xaxis.set_major_locator(xlocator)
        ax.xaxis.set_major_formatter(xformatter)

        plt.ylabel(key)

    # Trim excessive whitespace
    plt.tight_layout(pad=.5, w_pad=.5, h_pad=.5)

    # Exit on key q
    plt.figure(1).canvas.mpl_connect('key_press_event',
                                     lambda e:
                                     sys.exit(0) if e.key == 'ctrl+q'
                                                 else None)

    plt.show()

if __name__ == '__main__':
    plot_jsonl_data(sys.argv[1])

