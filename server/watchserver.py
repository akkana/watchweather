#!/usr/bin/env python3

from datetime import datetime, date, timedelta
from time import mktime
from math import ceil, floor

from flask import Flask, request, url_for, render_template, redirect, flash

# The code to keep track of our reporting stations:
import stations


# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')

# Don't map all whitespace/newlines in the jinja templates into
# whitespace in the HTML or JS:
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

# Need a secret key to use flash for error messages
app.config['SECRET_KEY'] = 'not really a secret'


@app.route('/')
def home_page():
    stations.initialize()

    now = datetime.now()

    return render_template('index.html',
                           title="Watch Weather: Menu",
                           stations=stations.stations)


@app.route('/stations')
def show_stations():
    """Display a page showing all currently reporting stations.
    """
    stations.initialize()

    return render_template('stations.html',
                           title="Watchweather: Stations Reporting",
                           refresh=60,
                           showkeys=[ 'temperature', 'humidity', 'rain_daily' ],
                           showstations=stations.stations)


@app.route('/details/<stationname>')
def details(stationname):
    """Show details in a big table for a specific station, or all
    """
    stations.initialize()

    if stationname == "all":
        title = "All Stations"
        showstations = stations.stations
    else:
        title = "%s Details" % stationname
        showstations = { stationname : stations.stations[stationname] }

    return render_template('details.html',
                           title=title,
                           stationname=stationname,
                           field_order = stations.get_field_order_fmt(),
                           showstations=showstations)


@app.route('/weekly/<stationname>', methods=['POST', 'GET'])
def weekly(stationname):
    """Summarize weekly details for a station
    """
    stations.initialize()

    try:
        data = stations.station_weekly(stationname)
    except KeyError as e:
        data = "No station named %s: %s" % (stationname, e)
    # XXX maybe add a case that catches other exceptions

    return render_template('timereport.html',
                           title="Weekly report for %s station" % stationname,
                           stationname=stationname,
                           data=data)


@app.route('/cumulative/<stationname>/<days>', methods=['POST', 'GET'])
@app.route('/cumulative/<stationname>/<days>/<chunkdays>',
           methods=['POST', 'GET'])
def cumulative(stationname, days, chunkdays=1):
    """Summarize details for a station for some time period.
       <days> can be an integer number of days,
       or week, month, year.
    """
    stations.initialize()

    try:
        days = int(days)
        title = "Last %d days report for %s station" % (days, stationname)
    except:
        title = "Past %s's report for %s station" % (days, stationname)

    if chunkdays == "month":
        title += " by month"
    elif chunkdays != 1:
        title += ", %s days at a time" % chunkdays

    try:
        data = stations.station_historic(stationname, days, chunkdays)
    except KeyError as e:
        data = "No station named %s: %s" % (stationname, e)
    # XXX maybe add a case that catches other exceptions

    return render_template('timereport.html',
                           title=title,
                           stationname=stationname,
                           field_order = stations.get_field_order(),
                           data=data)


# Some Jinja formatting filters

@app.template_filter('prettyname')
def prettyname_filter(s):
    try:
        return s.replace('_', ' ').title()
    except:
        return s


@app.template_filter('prettydata')
def prettydata_filter(x, fieldname=None, roundmore=False):
    """Jinja filter for displaying data: e.g. round to some sane level
    """
    if not x:
        return ''
    if type(x) is str:
        return x.replace('\n', '<br>')
    if type(x) is not float:
        return x
    if fieldname and "rain" in fieldname.lower():
        return "%.2f" % x
    elif roundmore:
        return "%d" % round(x)
    return "%.1f" % x


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
    try:
        dailydata = stations.read_daily_data(stationname, ['rain_daily'],
                                             st, et)
    except:
        flash("Sorry, don't have data to plot %s from %s to %s"
              % (stationname, st, et))
        return home_page()

    # More granular values may need resampling
    hourlydata = stations.read_csv_data_resample(stationname,
                                                 ['temperature',
                                                  'humidity',
                                                  'gust_speed',
                                                  'max_gust'],
                                                 st, et,
                                                 timedelta(hours=1))

    # chart.js needs Unix times * 1000 to feed to JavaScript's Date class.
    # I know it's tempting to give start and end time and let
    # the JS calculate it. But then the data can get out of sync
    # with the time. It's much easier to generate them from the
    # same function (in this case, read_csv_data_resample).
    dailydata['unixtimes'] = [ mktime(d.timetuple()) * 1000
                               for d in dailydata['t'] ]
    hourlydata['unixtimes'] = [ mktime(d.timetuple()) * 1000
                                for d in hourlydata['t'] ]

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
                           title="Weather Data for %s Station" % stationname,
                           lastreport=stations.last_station_update[stationname],
                           starttime=starttime, endtime=endtime,
                           dailydata=dailydata,
                           hourlydata=hourlydata)


@app.route('/api/compact/<stationname>')
def compact_data(stationname):
    """CURRENTLY ONLY A PLACEHOLDER.
       When implemented, this will 
    """
    stations.initialize()

    st = date(2023, 6, 1)
    et = date(2023, 7, 1)
    data = stations.read_csv_data_resample(stationname,
                                                 ['temperature',
                                                  'humidity',
                                                  'gust_speed',
                                                  'max_gust'],
                                           st, et,
                                           timedelta(hours=1))
    title = "Bogo-resample"
    from pprint import pprint
    pprint(data)

    return render_template('timereport.html',
                           title=title,
                           stationname=stationname,
                           field_order = stations.get_field_order(),
                           data=data)
