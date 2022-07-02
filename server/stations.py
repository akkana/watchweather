#!/usr/bin/env python3

# Manage a list of stations which are periodically reporting
# measured quantities such as temperature and humidity.

import os, sys
import json
import csv
from datetime import datetime, date, timedelta
import re


# The order in which to show fields.
# Read from ~/.config/watchweather/fields.
# There's one version with blanks in it, for pretty formatting,
# and another that's just the fields in order.
field_order = None
field_order_fmt = None


# A dictionary of dictionaries with various quantities we can report.
# The key in stations is station name.
# Dicts should include 'time' (datetime of last update).
# For example, station['office'] -> { 'temperature': 73, 'time': <datetime> }
# Values may be numbers or strings, but will normally be strings
# because that's what's sent in web requests.
stations = {}

# A dictionary of { "station_name": last_date }
last_station_update = {}

# How long to remember stations if they stop reporting.
expire_after = timedelta(minutes=5)

# Log files are named {savedir}/watchserver/clientname-YYYY-MM-DD
# and contain CSV lines, with only the fields specified in field_order.
# If logging isn't wanted, set this to None in initialize().
savedir = None

initialized = False


def initialize(expiration=None, savedir_path=None):
    """Initialize the station list.
       The optional expiration argument is a datetime.timedelta
       specifying how long to keep stations that stop reporting.
    """
    global savedir, initialized
    if initialized:
        return

    if savedir_path:
        savedir = savedir_path
    else:
        savedir = os.path.expanduser("~/.cache/watchserver")

    if not os.path.exists(savedir):
        try:
            os.makedirs(savedir)
        except:
            print("LOGGING DISABLED: can't open %s" % savedir, file=sys.stderr)
            savedir = None

    if expiration:
        expire_after = expiration

    # Populate last_station_update with a list of anything that
    # has an entry in the savedir.
    for csvfilename in os.listdir(savedir):
        # Valid filenames are like "Stationname-2021-08-27.csv"
        try:
            m = re.match(r'(.*)-(\d\d\d\d-\d\d-\d\d)\.csv', csvfilename)
            if not m:
                print("Illegal historic file", csvfilename, file=sys.stderr)
                continue
            stationname = m.group(1)
            # there's no date.strptime, alas
            filedate = datetime.strptime(m.group(2), '%Y-%m-%d').date()

        except Exception as e:
            print("Exception parsing filename %s: %s" % (csvfilename, e),
                  file=sys.stderr)
            continue

        if stationname in last_station_update:
            last_station_update[stationname] = max(
                last_station_update[stationname],
                filedate)
        else:
            last_station_update[stationname] = filedate

    # To get a list of bogus stations for testing, uncomment the next line:
    # populate_bogostations(5)

    initialized = True


def prettify(field):
    """Convert a field in the data into a user-visible field
    """
    return field.replace('_', ' ').title()


def populate_bogostations(nstations):
    """Create a specified number of  bogus stations to test the web server.
       If you want to test layout, you probably want to create at least 5.
    """
    import random

    stationnames = [ 'office', 'patio', 'garden', 'garage', 'kitchen',
                     'bedroom', 'roof', 'living room', 'Death Valley',
                     'Antarctica' ]
    nstations = min(nstations, len(stationnames))
    for st in stationnames[:nstations]:
        stations[st] = { 'temperature': "%.1f" % (random.randint(65, 102)),
                         'humidity':    "%.1f" % (random.randint(1, 100) / 100),
                         'time' :       datetime.now()
                       }


# The idiot python json module can't handle datetimes,
# so those have to be treated specially:
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))


def parse(val):
    """Take a value, which might be a str, float, datetime or int,
       and parse it if it's a float or datetime since those will
       need reformatting.
    """
    if type(val) is not str:
        return val
    try:
        return int(val)
    except:
        pass
    try:
        return float(val)
    except:
        pass
    try:
        return datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
    except:
        pass
    try:
        return datetime.strptime(val, '%Y-%m-%d %H:%M:%S.%f')
    except:
        pass
    try:
        return datetime.strptime(val, '%Y-%m-%d %H:%M')
    except:
        pass
    return val


def update_station(station_name, station_data):
    """Update a station, adding it if it's new.
       station_data is a dictionary.
       Also prune the list of stations.
    """
    global field_order, field_order_fmt

    # station_data is all strings since it came in through JSON.
    # Parse it to something more useful.
    for key in station_data:
        if type(station_data[key]) is str:
            station_data[key] = parse(station_data[key])

    stations[station_name] = station_data

    if not field_order:
        read_field_order_file()
    if not field_order:
        print("No field order file! Using keys from the first report.",
              sys.stderr)
        field_order = station_data.keys()
        field_order_fmt = field_order

    if savedir:
        # files are named clientname-YYYY-MM-DD
        datafilename = os.path.join(savedir,
                                    "%s-%s.csv" % (station_name,
                           station_data['time'].strftime("%Y-%m-%d")))
        there_already =  os.path.exists(datafilename)

        with open(datafilename, "a") as datafile:
            # Write a header if the file was just created:
            if not there_already:
                print(','.join(field_order), file=datafile)

            csvfields = []
            for field in field_order:
                if field == 'time':
                    csvfields.append(station_data[field].strftime("%Y-%m-%d %H:%M:%S"))
                elif field in station_data:
                    csvfields.append(str(station_data[field]))
                else:
                    csvfields.append('')
            print(','.join(csvfields), file=datafile)

        # To write in JSONL instead:
        # with open(datafilename, "a") as datafile:
        #     datafile.write(json.dumps(station_data, default=json_serial))
        #     datafile.write('\n')

    prune_stations()


def prune_stations():
    """Remove any station that hasn't reported in a while.
    """
    now = datetime.now()
    deleted_stations = []
    for stname in stations:
        try:
            if now - stations[stname]['time'] > expire_after:
                deleted_stations.append(stname)
        except KeyError:
            print("No 'time' in station", stname, sys.stderr)
            pass

    for d in deleted_stations:
        del stations[d]


def stations_summary():
    """Return an HTML string representing all the reporting stations.
       Only show temperature, humidity and rain_daily.
       XXX Eventually make this configurable.
    """
    outstr = ''
    showkeys = [ 'temperature', 'humidity', 'rain_daily' ]

    for stname in stations:
        st = stations[stname]

        outstr += """
<fieldset class="stationbox">

<legend>%s</legend>

<table class="datatable">
<tr>
""" % (stname)

        # keys = list(st.keys())

        # Keep the keys always in the same order.
        # Generally we want temperature first, so as a TEMPORARY measure,
        # use reverse sort. XXX Be smarter about order.
        # keys.sort(reverse=True)

        for key in showkeys:
            if key in st and st[key]:
                outstr += '  <td>%s\n' % key

        outstr += '<tr class="bigdata">'

        for key in showkeys:
            if key in st:
                # val = parse(st[key])
                val = st[key]

                if not val:
                    continue

                # Format floats to one decimal place,
                # except for rain which gets two.
                if type(val) is float:
                    if key == 'rain_daily':
                        strval = '%.2f' % val
                    else:
                        strval = '%.1f' % val
                else:
                    strval = str(val)

                # However, if it's a floating point, chances are it has
                # way too many decimal places. To avoid depending on all
                # modules to do that properly, guard against it here.
                outstr += '  <td>%s\n' % strval

        if 'time' in st:
            # Time will also likely need reformatting.
            # d = parse(st['time'])
            d = st['time']
            outstr += '<tr><td colspan=10>Last updated: %s' \
                                        % d.strftime('%H:%M')

        outstr += '</table>\n'
        outstr += '\n</fieldset>\n'

    return outstr


def station_details(stationname):
    """Show details for just one station"""

    fields = field_order_fmt

    html_out = '<table class="details">'
    extra_fields = ''
    # st = stations[stationname]
    if stationname == 'all':
        nstations = len(stations)
        showstations = stations
        html_out += '<tr><td class="station_name">'
        for stname in showstations:
            html_out += '<th class="val">%s' % (stname)
    else:
        nstations = 1
        showstations = { stationname: stations[stationname] }

    # If there was no fields file, just show all the fields we have,
    # in undefined order
    if not fields:
        fields = []
        for stname in showstations:
            for f in showstations[stname]:
                if f not in fields:
                    fields.append(f)

    # Collect the fields specified in field_order.
    for field in fields:
        if not field:
            html_out += '<tr><td colspan=%d>&nbsp;' % (nstations+1)
            continue

        html_out += '<tr>\n'
        html_out += '<td>%s\n' % prettify(field)
        for stname in showstations:
            st = showstations[stname]

            # Not all stations have all fields, so be prepared
            # for a KeyError:
            try:
                # Time should normally be datetime.
                # Rewrite time to get rid of decimal seconds
                # that would appear if we just did a string conversion:
                if field == 'time' and hasattr(st[field], 'strftime'):
                    valstr = st[field].strftime("%Y-%m-%d %H:%M:%S")
                elif type(st[field]) is float:
                    if field.startswith('rain'):
                        valstr = '%.2f' % st[field]
                    else:
                        valstr = '%.1f' % st[field]
                else:
                    valstr = str(st[field])

                html_out += '<td class="val">%s' % valstr
            except KeyError:
                html_out += '<td class="val">&nbsp;'

    html_out += '</table>'
    return html_out


class StatFields:
    def __init__(self):
        self.reset()

    def __repr__(self):
        if not self:
            return "<Empty StatFields>"
        return """StatFields:
total:   %.2f
number:  %d
average: %.2f
low:     %.2f
high:    %.2f""" % (self.total, self.n, self.average(), self.low, self.high)

    def __bool__(self):
        return (self.n > 0)

    def reset(self):
        self.total = 0
        self.n = 0
        self.low = sys.maxsize
        self.high = -sys.maxsize

    def accumulate(self, val):
        self.total += val
        self.n += 1
        self.low = min(self.low, val)
        self.high = max(self.high, val)

    def average(self):
        if not self.n:
            return None
        return self.total / self.n


def station_weekly(stationname):
    """Show a weekly summary for one station"""
    if not savedir:
        raise RuntimeError("No data dir, can't show a weekly summary")

    lastdate = last_station_update[stationname]

    # Look at last 7 days
    day = (lastdate - timedelta(days=7))

    # Fields that don't need any statistics: just take the last number.
    fields = ["rain_daily", "rain_event", "rain_monthly", "rain_yearly"]

    # A rainfall "event" means rain that has occurred without a break
    # of 24 hours or more. But that's tricky to calculate since the
    # most granular field is rain_hourly. So just use the last rain_daily
    # value for each day.
    rainfall_event = 0.
    last_rain_day = date(1970, 1, 1)

    # clientname-YYYY-MM-DD
    html = ""
    while day <= lastdate:
        daystr = day.strftime("%Y-%m-%d")
        datafilename = os.path.join(savedir,
                                    "%s-%s.csv" % (stationname, daystr))
        # Show highs and lows for these fields
        highlowfields = {"temperature": StatFields(),
                         "average_wind": StatFields(),
                         "gust_speed": StatFields()
                        }
        # For some fields, lows are meaningless, it's always zero
        highs_only = ("average_wind", "gust_speed")
        with open(datafilename, "r") as datafp:
            reader = csv.DictReader(datafp)
            for row in reader:
                for f in highlowfields:
                    try:
                        val = float(row[f])
                    except:
                        continue
                    highlowfields[f].accumulate(val)

        # The last row contains the rainfall for the day
        if 'rain_daily' in row and row['rain_daily']:
            row['rain_daily'] = float(row['rain_daily'])
        if row['rain_daily']:
            rainfall_event += row['rain_daily']
            last_rain_day = day
        else:
            rainfall_event = 0.
        row["rain_event"] = rainfall_event

        # Ready to output this day

        # First the table start, if it hasn't been added already:
        if not html:
            html = "\n<table class=\"details\"><tbody>\n<tr><th>Day "
            for f in fields:
                html += "<th>%s " % prettify(f)
            for f in highlowfields:
                if f not in highs_only:
                    html += "<th>%s<br>Low " % prettify(f)
                html += "<th>%s<br>High " % prettify(f)
            html += "</tr>\n"

        html += "<tr><td>%s " % str(day)

        # take "fields" from only the last row,
        for f in fields:
            if f in row and row[f]:
                html += "<td>%.2f" % float(row[f])
            else:
                html += "<td>&nbsp;"

        for f in highlowfields:
            if f not in highs_only:
                if highlowfields[f].low < sys.maxsize:
                    html += "<td>%.1f" % highlowfields[f].low
                else:
                    html += "<td>&nbsp;"
            if highlowfields[f].high > 0:
                html += "<td>%.1f" % highlowfields[f].high
            else:
                html += "<td>&nbsp;"
        html += "\n"

        day += timedelta(days=1)

    html += "</tbody></table>\n"
    return html


def read_csv_file(filename):
    with open(filename, "r") as datafp:
        reader = csv.DictReader(datafp)
        return [ row for row in reader ]


#
# Annoyingly, datetime doesn't offer a straightforward method
# for ensuring something is either a date or a datetime.
#
def to_day(dt):
    """Given datetime or date, return date"""
    if type(dt) is date:
        return dt
    return dt.date()


def to_datetime(d):
    """Given datetime or date, return datetime"""
    if type(d) is datetime:
        return d
    if type(d) is date:
        return datetime.combine(d, datetime.min.time())
    raise RuntimeError("Can't convert %s to datetime" % type(d))


def read_daily_data(stationname, valtypes, start_date, end_date):
    """Read the values from csv files that are already accumulated
       and so should not be summed,
       notably rain_daily and rain_event.
       No need to specify a time increment: it's always days.
       Return: {
           't':        [list of datetimes],
           'valtype1': [list of floats], ...
       }
    """
    retdata = { 't': [] }
    for vt in valtypes:
        retdata[vt] = []

    day = to_day(start_date)
    end_date = to_day(end_date)
    csvreader = None
    oneday = timedelta(days=1)

    while day <= end_date:
        daystr = day.strftime("%Y-%m-%d")
        datafile = os.path.join(savedir,
                                "%s-%s.csv" % (stationname, daystr))

        try:
            datafp = open(datafile)
            csvreader = csv.DictReader(datafp)
            for row in csvreader:
                continue
            datafp.close()

            # Now row is the last row.
            retdata['t'].append(day)
            for vt in valtypes:
                try:
                    retdata[vt].append(float(row[vt]))
                except KeyError:
                    pass

        except FileNotFoundError:
            print("Skipping", day, ": no data file", sys.stderr)
            csvreader = None

        day += oneday

    # Were there any keys not found?
    for vt in valtypes:
        if vt not in retdata:
            print(f"Warning: no '{vt}' in the data", sys.stderr)

    if datafp:
        datafp.close()

    return retdata


def read_csv_data_resample(stationname, valtypes,
                           start_time, end_time, time_incr):
    """Read the values from valtypes in from csv files,
       resampling to have values every time_incr (a datetime.timedelta)
       Return: {
           't':        [list of datetimes],
           'valtype1': [list of floats], ...
       }
    """
    retdata = { 't': [] }
    statdata = {}
    for vt in valtypes:
        retdata[vt] = []
        statdata[vt] = StatFields()   # has n, total, low, high

    def average_this_interval():
        retdata["t"].append(t0)
        for vt in valtypes:
            if statdata[vt]:
                retdata[vt].append(statdata[vt].average())
            else:
                retdata[vt].append(None)

            statdata[vt].reset()

    t0 = to_datetime(start_time)
    t = t0
    t1 = t0 + time_incr
    csvreader = None
    day = None
    datafp = None

    while t <= end_time:
        if not csvreader:
            if datafp:
                datafp.close()
            day = to_day(t0)
            daystr = day.strftime("%Y-%m-%d")
            datafile = os.path.join(savedir,
                                    "%s-%s.csv" % (stationname, daystr))

            try:
                datafp = open(datafile)
                csvreader = csv.DictReader(datafp)
            except FileNotFoundError:
                print("Skipping", day, ": no data file", sys.stderr)
                csvreader = None

                # That means there's no data for this day,
                # so skip forward a day.
                t0 = to_datetime(day) + timedelta(days=1)
                if t0 >= end_time:
                    break
                t1 = t0 + time_incr
                if t1 > end_time:
                    t1 = end_time
                continue

        # Now there's definitely a csvreader object
        try:
            row = next(csvreader)
        except StopIteration:
            csvreader = None
            t0 += time_incr
            # Loop around and try again
            continue

        t = datetime.strptime(row['time'], "%Y-%m-%d %H:%M:%S")
        if t < t0:
            continue

        if t >= t1:
            # end of interval:
            # compute averages and save the new data items
            average_this_interval()

            t0 += time_incr
            t1 = t0 + time_incr
            if t1 > end_time:
                t1 = end_time

        # Whether a new interval or old, accumulate this row.
        for vt in valtypes:
            statdata[vt].accumulate(float(row[vt]))

    # Save the final averages
    if statdata[valtypes[0]]:
        average_this_interval()

    if datafp:
        datafp.close()

    return retdata


def read_field_order_file():
    global field_order, field_order_fmt

    configfile = os.path.expanduser("~/.config/watchweather/fields")

    try:
        fp = open(configfile)
    except:
        return

    if not field_order_fmt:
        field_order_fmt = []

    for line in fp:
        line = line.strip()
        if line.startswith('#'):
            continue
        field_order_fmt.append(line)

    fp.close()

    field_order = [ f for f in field_order_fmt if f ]


if __name__ == '__main__':
    initialize()
    print(stations_as_html())

