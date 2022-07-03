#!/usr/bin/env python3

from datetime import datetime, date, timedelta
from time import mktime
from math import ceil, floor

from flask import Flask, request, url_for, render_template

# The code to keep track of our reporting stations:
import stations


# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')


@app.route('/')
def home_page():
    stations.initialize()

    today = date.today()

    def station_row(stname):
        if (stname not in stations.last_station_update or
            today - stations.last_station_update[stname] > timedelta(days=7)):
            style = "historic"
        else:
            style = "current"
        return '<tr class="%s"><th>%s</th>\n' \
                '  <td><a href="/details/%s">Details</a></td>\n' \
                '  <td><a href="/weekly/%s">Weekly</a></td>\n' \
                '  <td><a href="/plot/%s">Plots</a></td>\n' \
                '  <td>(last updated %s)</td></tr>\n' \
                % (style, stname, stname, stname, stname,
                   stations.last_station_update[stname])

    htmlcontent = ""

    for stname in stations.stations:
        htmlcontent += station_row(stname)
    for stname in stations.last_station_update:
        if stname not in stations.stations:
            htmlcontent += station_row(stname)

    # To pass HTML to a jinja template without escaping it,
    # the template must use: {{ htmlcontent|safe }}
    return render_template('index.html',
                           title="Watchweather: Menu",
                           htmlcontent=htmlcontent)


@app.route('/stations')
def show_stations():
    """Display a page showing all currently reporting stations.
    """
    stations.initialize()

    htmlcontent=stations.stations_summary()
    print(htmlcontent)

    return render_template('stations.html',
                           title="Watchweather: Stations Reporting",
                           refresh=30,
                           htmlcontent=htmlcontent)


@app.route('/details/<stationname>')
def details(stationname):
    """Show details in a big table for a specific station, or all
    """
    stations.initialize()

    try:
        details = stations.station_details(stationname)
    except KeyError:
        details = "No station named %s" % stationname

    if stationname == "all":
        title = "All Stations"
    else:
        title = "%s Details" % stationname

    return render_template('details.html',
                           title=title,
                           htmlcontent=details)


@app.route('/weekly/<stationname>', methods=['POST', 'GET'])
def weekly(stationname):
    """Summarize weekly details for a station
    """
    stations.initialize()

    try:
        htmlcontent = stations.station_weekly(stationname)
    except KeyError as e:
        htmlcontent = "No station named %s: %s" % (stationname, e)
    # XXX maybe add a case that catches other exceptions

    return render_template('details.html',
                           title="Weekly report for %s station" % stationname,
                           htmlcontent=htmlcontent)


@app.route('/report/<stationname>', methods=['POST', 'GET'])
def report(stationname):
    """Accept a report over http from one station.
       Real clients generally use POST, but the unittest test app uses GET.
    """
    stations.initialize()

    # request.form is type ImmutableMultiDict, which isn't too useful:
    # first, it's immutable, and second, indexed items seem to be
    # lists of strings instead of just strings, though this doesn't
    # seem to be documented anywhere.
    # Turn it into a normal dictionary like we use in stations.py:
    vals = request.form.to_dict()

    # If it doesn't have a last-updated time, add one:
    vals['time'] = datetime.now()

    stations.update_station(stationname, vals)

    retstr = 'Content-type: text/plain\n\n'
    for key in request.form:
        retstr += '%s: %s\n' % (key, request.form[key])
    return retstr


@app.route('/plot/<stationname>', methods=['POST', 'GET'])
def plot(stationname):
    """Plot weather for a station.
       Currently only plots rain.
    """
    stations.initialize()

    today = date.today()
    now = datetime.now()

    # Plotting a daily value is easy
    dailydata = stations.read_daily_data(stationname, ['rain_daily'],
                                         today - timedelta(days=7), today)

    # More granular values may need resampling
    hourlydata = stations.read_csv_data_resample(stationname, ['temperature'],
                                                 today - timedelta(days=30),
                                                 now,
                                                 timedelta(hours=1))
    # charts.js can't do auto scaling, and jinja can't do max, so
    # calculate it here, rounded up to multiples of roundoff.
    def set_chart_maxmin(data, key, roundoff=1):
        if not data[key]:
            data[f'{key}_max'] = 1
            data[f'{key}_min'] = 0
            return

        data[f'{key}_max'] = ceil(max([x for x in data[key] if x])
                                  / roundoff) * roundoff
        data[f'{key}_min'] = floor(min([x for x in data[key] if x])
                                  / roundoff) * roundoff

    set_chart_maxmin(dailydata, 'rain_daily', .1)
    set_chart_maxmin(hourlydata, 'temperature', 1)

    # chart.js needs Unix times * 1000 to feed to JavaScript's Date class.
    dailydata['unixtimes'] = [ mktime(d.timetuple()) * 1000
                               for d in dailydata['t'] ]
    hourlydata['unixtimes'] = [ mktime(d.timetuple()) * 1000
                                for d in hourlydata['t'] ]

    return render_template('plots.html',
                           stationname=stationname,
                           lastreport=stations.last_station_update[stationname],
                           dailydata=dailydata,
                           hourlydata=hourlydata)

