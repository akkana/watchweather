#!/usr/bin/env python3

from flask import Flask, request, url_for
import datetime

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')

# A list of dictionaries with various quantities we can report,
# which must include "name" and should include 'time' (datetime of last update).
# For example, station[0] might be { 'name': office, 'temperature': 73 }
# Values may be numbers or strings.
stations = []

def populate_bogostations():
    stations.append({ 'name': 'office',     'temperature': 73, 'humidity': 10 })
    stations.append({ 'name': 'patio',      'temperature': 73, 'humidity': 6 })
    stations.append({ 'name': 'bedroom',    'temperature': 73, 'humidity': 9 })
    stations.append({ 'name': 'guest room', 'temperature': 73, 'humidity': 12 })
    stations.append({ 'name': 'garden',     'temperature': 73, 'humidity': 4 })
    stations.append({ 'name': 'kitchen',    'temperature': 73, 'humidity': 7 })
    for st in stations:
        st['time'] = datetime.datetime.now()

populate_bogostations()

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
</html>''' % stations_as_html()

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

