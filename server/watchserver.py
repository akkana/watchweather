#!/usr/bin/env python3

from datetime import datetime, date, timedelta

from flask import Flask, request, url_for

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

    html += '<h3>Weekly Data:</h3>\n<ul>'
    today = date.today()
    for stname in stations.historic_stations:
        if today - stations.historic_stations[stname] > timedelta(days=7):
            style = "historic"
        else:
            style = "current"
        html += '<li class="%s"><a href="/weekly/%s">%s Weekly</a> ' \
                '(last updated %s)</li>\n' \
            % (style, stname, stname, stations.historic_stations[stname])

    html += "</ul>\n" + HTML_footer()
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
