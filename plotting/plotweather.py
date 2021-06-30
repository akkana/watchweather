#!/usr/bin/env python3

# Most useful tutorial: https://plotly.com/python/line-charts/

import sys, os
import csv
from datetime import datetime, timedelta

import plotly.graph_objects as go

DATADIR = os.path.expanduser("~/moontrade/watchweather-data/")


date_labels = []
day_numbers = {}

def set_up_days():
    """Generate some data structures that will be used to insert
       dated observations into an ordered list.
    """
    # Generate date names.
    # Use a leap year so there's a space for Feb 29.
    LEAPYEAR = 2020
    thedate = datetime(LEAPYEAR, 1, 1)
    while thedate.year == LEAPYEAR:
        day_numbers[(thedate.month, thedate.day)] = len(date_labels)
        date_labels.append(thedate.strftime("%b %d"))
        thedate += timedelta(days=1)

set_up_days()


def read_highs_lows(stationname, start_date, end_date, field):
    """Read data from data files representing the given date range,
       and save the daily highs and lows.
       stationname is the string used in the CSV filenames.
       start_date and end_date are datetime.datetime.
       fields is a list of named fields to be read from the CSV.
       Return a dict of ...
    """

    # structures to hold the data.
    # year_data[2021]["high field"] = []
    # date_labels = ["Jan 1", ..., "Dec 31"]
    year_data = {}

    minindex = field + " min"
    maxindex = field + " max"

    thedate = start_date
    while thedate < end_date:
        year = thedate.year
        if year not in year_data:
            year_data[year] = { minindex: [None]*366, maxindex: [None]*366 }

        filename = thedate.strftime("Outdoor-%Y-%m-%d.csv")
        low = sys.float_info.max
        high = sys.float_info.min
        try:
            with open(os.path.join(DATADIR, filename)) as datafp:
                reader = csv.DictReader(datafp)
                for row in reader:
                    try:
                        # DictReader reads in strings, not floats
                        val = float(row[field])
                        low = min(low, val)
                        high = max(high, val)
                    except (ValueError, TypeError):
                        # print(f"Missing %s data on %s"
                        #       % (field, thedate.strftime('%y-%m-%d')))
                        # print(row)
                        continue

            # Done reading the day's data. Save it.
            daynum = day_numbers[(thedate.month, thedate.day)]
            if low < sys.float_info.max:
                year_data[year][minindex][daynum] = low
            if high > sys.float_info.min:
                year_data[year][maxindex][daynum] = high

        except FileNotFoundError:
            pass

        thedate += timedelta(days=1)

    return date_labels, year_data


if __name__ == '__main__':
    date_labels, year_data = read_highs_lows("Outdoor",
                                             datetime(2019, 1, 1),
                                             datetime(2021, 6, 29),
                                             "temperature")

    fig = go.Figure()

    reds = ('orange', 'firebrick', 'red')
    blues = ('aquamarine', 'slateblue', 'blue')

    for i, year in enumerate((2019, 2020, 2021)):
        fig.add_trace(go.Scatter(x=date_labels,
                                 y=year_data[year]["temperature max"],
                                 name='High %d' % year,
                                 connectgaps=True,
                                 line=dict(color=reds[i], width=4)))
        fig.add_trace(go.Scatter(x=date_labels,
                                 y=year_data[year]["temperature min"],
                                 name='Low %s' % year,
                                 connectgaps=True,
                                 line=dict(color=blues[i], width=4)))

    fig.update_layout(title='Daily High and Low Temperatures in La Senda',
                      xaxis_title='Date',
                      yaxis_title='Temperature (degrees F)')


fig.show()
