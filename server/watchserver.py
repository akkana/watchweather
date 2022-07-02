#!/usr/bin/env python3

from datetime import datetime, date, timedelta
from time import mktime
from math import ceil, floor

from flask import Flask, request, url_for, render_template

# The code to keep track of our reporting stations:
import stations


# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')


def HTML_header(title, refresh=0, stylesheets=None):
    """Boilerplate HTML headers
    """

    if not stylesheets:
        stylesheets = ["/basic.css"]

    html = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1">"""
    if refresh:
        html += '<meta http-equiv="refresh" content="%d">' % refresh
    html += """
<title>%s</title>
""" % (title)
    for sheet in stylesheets:
        html += '<link rel="stylesheet" type="text/css" href="%s" />\n' % sheet

    html += """
</head>

<body>

<h1>%s</h1>""" % (title)

    return html


def HTML_footer(stationname=None):
    if stationname and stationname != "all":
        stationdetails = '<a href="/details/%s">%s Station Details</a> |\n' \
            % (stationname, stationname)
        stationweekly = '<a href="/weekly/%s">%s Station Week Summary</a> |\n' \
            % (stationname, stationname)
        stationweekly = '<a href="/plot/%s">%s Station Plots</a> |\n' \
            % (stationname, stationname)
    else:
        stationdetails = ""
        stationweekly = ""

    return """
<hr>
<a href="/stations">Summary</a> |
%s<a href="/details/all">All Station Details</a> |
%s<a href="/">Menu</a>
</body>
</html>
""" % (stationdetails, stationweekly)


@app.route('/')
def home_page():
    stations.initialize()

    html = HTML_header("Watch Weather")

    html += """<p>\n<a href="/stations">Summary of all Stations</a>
<p>
<a href="/details/all">Detailed View of all Stations</a>

<h3>Individual Stations:</h3>

<table class="menu">
"""

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

    for stname in stations.stations:
        html += station_row(stname)
    for stname in stations.last_station_update:
        if stname not in stations.stations:
            html += station_row(stname)

    html += "</table>\n" + HTML_footer()
    return html


@app.route('/stations')
def show_stations():
    """Display a page showing all currently reporting stations.
    """
    stations.initialize()

    html_out = HTML_header("Watchweather: Stations Reporting", refresh=30,
                           stylesheets=["basic.css", "wrap.css"])
    html_out += stations.stations_summary()
    html_out += HTML_footer()
    return html_out


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

    html_out = HTML_header(title)
    html_out += details
    html_out += HTML_footer(stationname)

    return html_out


@app.route('/weekly/<stationname>', methods=['POST', 'GET'])
def weekly(stationname):
    """Summarize weekly details for a station"""
    stations.initialize()

    try:
        details = stations.station_weekly(stationname)
    except KeyError as e:
        details = "No station named %s: %s" % (stationname, e)
    # XXX maybe add a case that catches other exceptions

    html_out = HTML_header("Weekly report for %s station" % stationname)
    html_out += details
    html_out += HTML_footer(stationname)

    return html_out


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

