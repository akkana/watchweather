#!/usr/bin/env python3

from datetime import datetime, date, timedelta
from time import mktime
from math import ceil, floor

from flask import Flask, request, url_for, render_template

# The code to keep track of our reporting stations:
import stations


# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')

# Don't map all whitespace/newlines in the jinja templates into
# whitespace in the HTML or JS:
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True


@app.route('/')
def home_page():
    stations.initialize()

    now = datetime.now()

    def station_row(stname):
        if (stname not in stations.last_station_update or
            now - stations.last_station_update[stname] > timedelta(days=7)):
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
                           stationname=stationname,
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


@app.route('/plot/<stationname>')
@app.route('/plot/<stationname>/<starttime>')
@app.route('/plot/<stationname>/<starttime>/<endtime>')
def plot(stationname, starttime=None, endtime=None):
    """Plot weather for a station.
       By default, print the last 30 days, unless starttime and endtime are set.
       If only startime is specified, run from starttime to now.
       All times specified as yyyy-mm-dd or yyyy-mm-ddTHH:MM
    """
    stations.initialize()

    today = date.today()
    now = datetime.now()

    # Set start and end times to what JavaScript needs: unix time * 1000.
    if endtime == 'week':
        et = today
    else:
        try:
            et = datetime.strptime(endtime, '%Y-%m-%dT%H:%M')
        except:
            try:
                et = datetime.strptime(endtime, '%Y-%m-%d')
            except:
                et = now
    endtime = mktime(et.timetuple()) * 1000

    if starttime == 'week':
        st = et - timedelta(days=7)
    else:
        try:
            st = datetime.strptime(starttime, '%Y-%m-%dT%H:%M')
        except:
            try:
                st = datetime.strptime(starttime, '%Y-%m-%d')
            except:
                st = today - timedelta(days=30)
    starttime = mktime(st.timetuple()) * 1000
    # Now st and et are datetimes, starttime and endtime are unix time.

    # Plotting a daily value is easy
    dailydata = stations.read_daily_data(stationname, ['rain_daily'],
                                         st, et)

    # More granular values may need resampling
    hourlydata = stations.read_csv_data_resample(stationname,
                                                 ['temperature',
                                                  'humidity',
                                                  'gust_speed',
                                                  'max_gust'],
                                                 st, et,
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

    # Set min and max for anything we want plotted.
    set_chart_maxmin(dailydata, 'rain_daily', .1)
    set_chart_maxmin(hourlydata, 'temperature', 1)
    set_chart_maxmin(hourlydata, 'humidity', 1)
    # set_chart_maxmin(hourlydata, 'gust_speed', 1)
    set_chart_maxmin(hourlydata, 'max_gust', 1)
    hourlydata['gust_speed_min'] = hourlydata['max_gust_min']
    hourlydata['gust_speed_max'] = hourlydata['max_gust_max']

    return render_template('plots.html',
                           stationname=stationname,
                           lastreport=stations.last_station_update[stationname],
                           starttime=starttime, endtime=endtime,
                           dailydata=dailydata,
                           hourlydata=hourlydata)

