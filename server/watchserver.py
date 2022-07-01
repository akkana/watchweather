#!/usr/bin/env python3

from datetime import datetime, date, timedelta
from time import mktime
from math import ceil

from flask import Flask, request, url_for, render_template

# The code to keep track of our reporting stations:
import stations

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')

stations.initialize()


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
    html = HTML_header("Watch Weather")

    html += """<p>\n<a href="/stations">Summary of all Stations</a>
<p>
<a href="/details/all">Detailed View of all Stations</a>

<h3>Individual Stations:</h3>
<ul>"""

    for stname in stations.stations:
        html += '<li><a href="/details/%s">%s Details</a>' % (stname, stname)

    html += '</ul>'

    html += '<h3>Historic Data:</h3>\n<table class="menu">\n'
    today = date.today()
    for stname in stations.last_station_update:
        if today - stations.last_station_update[stname] > timedelta(days=7):
            style = "historic"
        else:
            style = "current"
        html += '<tr class="%s"><th>%s</th>\n' \
                '  <td><a href="/weekly/%s">Weekly</a></td>\n' \
                '  <td><a href="/plot/%s">Plots</a></td>\n' \
                '  <td>(last updated %s)</td></tr>\n' \
                % (style, stname, stname, stname,
                   stations.last_station_update[stname])

    html += "</table>\n" + HTML_footer()
    return html


@app.route('/stations')
def show_stations():
    """Display a page showing all currently reporting stations.
    """
    html_out = HTML_header("Watchweather: Stations Reporting", refresh=30,
                           stylesheets=["basic.css", "wrap.css"])
    html_out += stations.stations_summary()
    html_out += HTML_footer()
    return html_out


@app.route('/details/<stationname>')
def details(stationname):
    """Show details in a big table for a specific station, or all"""

    try:
        details = stations.station_details(stationname)
    except KeyError:
        details = "No station named %s" % stationname

    if stationname == "all":
        title = "All Stations"
    else:
        title = stationname

    html_out = HTML_header(title)
    html_out += details
    html_out += HTML_footer(stationname)

    return html_out


@app.route('/weekly/<stationname>', methods=['POST', 'GET'])
def weekly(stationname):
    """Summarize weekly details for a station"""
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
    """
    if request.method == 'POST':
        print("Got a report from %s including:" % stationname,
              ', '.join(list(request.form.keys())))

        # request.form is type ImmutableMultiDict, which isn't too useful:
        # first, it's immutable, and second, indexed items seem to be
        # lists of strings instead of just strings, though this doesn't
        # seem to be documented anywhere.
        # Turn it into a normal dictionary like we use in stations.py:
        vals = request.form.to_dict()

        # If it doesn't have a last-updated time, add one:
        vals['time'] = datetime.now()

        stations.update_station(stationname, vals)

        retstr = ''
        for key in request.form:
            retstr += '%s: %s\n' % (key, request.form[key])
        return retstr

    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return "Error: request.method was %s" % request.method


@app.route('/plot/<stationname>', methods=['POST', 'GET'])
def plot(stationname):
    """Plot weather for a station.
       Currently only plots rain.
    """

    today = date.today()

    # Plotting a daily value is easy
    data = stations.read_daily_data(stationname, ['rain_daily'],
                                    today - timedelta(days=7), today)

    # stations.read_csv_data_resample(stationname, valtypes,
    #                        start_time, end_time, time_incr)

    # charts.js can't do auto scaling, and jinja can't do max, so
    # calculate it here, rounded up to multiples of roundoff.
    def set_chart_max(key, roundoff=1):
        data[f'{key}_max'] = ceil(max(data[key]) / roundoff) * roundoff
    set_chart_max('rain_daily', .1)

    # chart.js needs Unix times * 1000 to feed to JavaScript's Date class.
    data['unixtimes'] = [ mktime(d.timetuple()) * 1000
                          for d in data['t'] ]

    return render_template('plots.html',
                           title='Weather data for %s' % stationname,
                           data=data)

