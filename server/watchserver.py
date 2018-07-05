#!/usr/bin/env python3

from flask import Flask, request, url_for

import datetime

# The code to keep track of our reporting stations:
import stations

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')

stations.initialize()

@app.route('/')
def show_stations():
    '''Display a page showing all currently reporting stations.
    '''
    return '''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="30">

<title>Stations Reporting</title>
<link rel="stylesheet" type="text/css" href="/wrap.css" />
</head>

<body>

<h1>Stations Reporting</h1>

%s

</body>
</html>''' % stations.stations_as_html()

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

