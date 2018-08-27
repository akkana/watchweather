#!/usr/bin/env python3

import datetime

from flask import Flask, request, url_for

# The code to keep track of our reporting stations:
import stations

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')

stations.initialize()

def HTML_header(title, refresh=0, stylesheets=None):
    '''Boilerplate HTML headers. I know flask is supposed to have
       templating but I haven't figured it out yet.
    '''

    if not stylesheets:
        stylesheets = ["/basic.css"]

    html = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1">'''
    if refresh:
        html += '<meta http-equiv="refresh" content="%d">' % refresh
    html += '''
<title>%s</title>
''' % (title)
    for sheet in stylesheets:
        html += '<link rel="stylesheet" type="text/css" href="%s" />\n' % sheet

    html += '''
</head>

<body>

<h1>%s</h1>''' % (title)

    return html

def HTML_footer():
    return '''
<hr>
<a href="/stations">Summary</a> |
<a href="/details/all">Details</a> |
<a href="/">Menu</a>
</body>
</html>
'''

@app.route('/')
def home_page():
    html = HTML_header("Watch Weather")

    html += '''<p>\n<a href="/stations">Summary of all Stations</a>
<p>
<a href="/details/all">Detailed View of all Stations</a>

<h3>Individual Stations:</h3>
<ul>'''

    for stname in stations.stations:
        html += '<li><a href="/details/%s">%s Details</a>' % (stname, stname)

    html += '</ul>'

    html += HTML_footer()
    return html

@app.route('/stations')
def show_stations():
    '''Display a page showing all currently reporting stations.
    '''
    html_out = HTML_header("Stations Reporting", refresh=30,
                           stylesheets=["basic.css", "wrap.css"])
    html_out += stations.stations_summary()
    html_out += HTML_footer()
    return html_out

@app.route('/details/<stationname>')
def details(stationname):
    '''Show details in a big table for a specific station, or all'''

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
    html_out += HTML_footer()

    return html_out

@app.route('/report/<stationname>', methods=['POST', 'GET'])
def report(stationname):
    '''Accept a report over http from one station.
    '''
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
        vals['time'] = datetime.datetime.now()

        stations.update_station(stationname, vals)

        retstr = ''
        for key in request.form:
            retstr += '%s: %s\n' % (key, request.form[key])
        return retstr

    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return "Error: request.method was %s" % request.method

