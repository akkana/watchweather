#!/usr/bin/env python3

from flask import Flask, request, url_for

import datetime

# The code to keep track of our reporting stations:
import stations

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')

stations.initialize()

def stations_as_html():
    outstr = ''
    for st in stations:
        if 'name' not in st:
            continue

        outstr += '''
<fieldset class="stationbox">

<legend>%s</legend>

<table class="datatable">
<tr>
''' % (st['name'])
        for key in st:
            if key == 'name' or key == 'time':
                continue
            outstr += '  <td>%s\n' % key
        outstr += '<tr class="bigdata">'

        for key in st:
            if key == 'name' or key == 'time':
                continue
            outstr += '  <td>%s\n' % st[key]

        if 'time' in st:
            outstr += '<tr><td colspan=10>'
            if hasattr(st['time'], 'strftime'):
                outstr += "Last updated: " + st['time'].strftime('%H:%M')
            else:
                outstr += "Last updated: " + st['time']

        outstr += '</table>\n'
        outstr += '\n</fieldset>\n'

    return outstr

@app.route('/')
def show_stations():
    return '''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<title>Stations Reporting</title>
<link rel="stylesheet" type="text/css" href="/wrap.css" />
</head>

<body>

<h1>Stations Reporting</h1>

%s

</body>
</html>''' % stations.stations_as_html()

@app.route('/post/<int:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return 'Post %d' % post_id

@app.route('/report1/<stationname>')
def report1(stationname):
    return "Report from %s" % stationname

@app.route('/report/<stationname>', methods=['POST', 'GET'])
def report(stationname):
    if request.method == 'POST':
        print("Got a report:", request, request.form)
        print("Keys:", ', '.join(list(request.form.keys())))

        # request.form is type ImmutableMultiDict, which isn't too useful:
        # first, it's immutable, and second, indexed items seem to be
        # lists of strings instead of just strings, though this doesn't
        # seem to be documented anywhere.
        # Turn it into a normal dictionary like we use in stations.py:
        vals = request.form.to_dict()

        # Make sure we have a station name:
        if 'name' not in vals:
            print("Adding name", stationname)
            vals['name'] = stationname

        # If it doesn't have a last-updated time, add one:
        vals['time'] = datetime.datetime.now()

        stations.add_station(vals)

        retstr = ''
        for key in request.form:
            retstr += '%s: %s\n' % (key, request.form[key])
        print("Returning:'''%s'''" % retstr)
        return retstr

    #     if valid_login(request.form['username'],
    #                    request.form['password']):
    #         return log_the_user_in(request.form['username'])
    #     else:
    #         error = 'Invalid username/password'

    # the code below is executed if the request method
    # was GET or the credentials were invalid
    # return render_template('login.html', error=error)
    return "Error: request.method was %s" % request.method

