#!/usr/bin/env python3

# Manage a list of stations which are periodically reporting
# measured quantities such as temperature and humidity.

import datetime
import os
import json

# The order in which to show fields.
# Read from ~/.config/watchweather/fields.
# There's one version with blanks in it, for pretty formatting,
# and another that's just the fields in order.
field_order = None
field_order_fmt = None

# Log files are named ~/.cache/watchserver/clientname-YYYY-MM-DD
# and contain CSV lines, with only the fields specified in field_order.
# If logging isn't wanted, set this to None.
savedir = os.path.expanduser("~/.cache/watchserver")
if not os.path.exists(savedir):
    try:
        os.makedirs(savedir)
    except:
        print("LOGGING DISABLED: can't open %s" % savedir)
        savedir = None

# A dictionary of dictionaries with various quantities we can report.
# The key in stations is station name.
# Dicts should include 'time' (datetime of last update).
# For example, station['office'] -> { 'temperature': 73, 'time': <datetime> }
# Values may be numbers or strings, but will normally be strings
# because that's what's sent in web requests.
stations = {}

# How long to remember stations if they stop reporting.
expire_after = datetime.timedelta(minutes=5)

def initialize(expiration=None):
    '''Initialize the station list.
       The optional expiration argument is a datetime.timedelta
       specifying how long to keep stations that stop reporting.
    '''
    if expiration:
        expire_after = expiration

    # To get a list of bogus stations for testing, uncomment the next line:
    # populate_bogostations(5)

def populate_bogostations(nstations):
    '''Create a specified number of  bogus stations to test the web server.
       If you want to test layout, you probably want to create at least 5.
    '''
    import random

    stationnames = [ 'office', 'patio', 'garden', 'garage', 'kitchen',
                     'bedroom', 'roof', 'living room', 'Death Valley',
                     'Antarctica' ]
    nstations = min(nstations, len(stationnames))
    for st in stationnames[:nstations]:
        stations[st] = { 'temperature': "%.1f" % (random.randint(65, 102)),
                         'humidity':    "%.1f" % (random.randint(1, 100) / 100),
                         'time' :       datetime.datetime.now()
                       }

# The idiot python json module can't handle datetimes,
# so those have to be treated specially:
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

def parse(val):
    '''Take a value, which might be a str, float, datetime or int,
       and parse it if it's a float or datetime since those will
       need reformatting.
    '''
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
        return datetime.datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
    except:
        pass
    try:
        return datetime.datetime.strptime(val, '%Y-%m-%d %H:%M:%S.%f')
    except:
        pass
    try:
        return datetime.datetime.strptime(val, '%Y-%m-%d %H:%M')
    except:
        pass
    return val

def update_station(station_name, station_data):
    '''Update a station, adding it if it's new.
       station_data is a dictionary.
       Also prune the list of stations.
    '''
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
        print("No field order file! Using keys from the first report.")
        field_order = station_data.keys()
        field_order_fmt = field_order

    if savedir:
        # clientname-YYYY-MM-DD
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
    '''Remove any station that hasn't reported in a while.
    '''
    now = datetime.datetime.now()
    deleted_stations = []
    for stname in stations:
        try:
            if now - stations[stname]['time'] > expire_after:
                deleted_stations.append(stname)
        except KeyError:
            print("No 'time' in station", stname)
            pass

    for d in deleted_stations:
        del stations[d]

def stations_summary():
    '''Return an HTML string representing all the reporting stations.
       Only show temperature, humidity and rain_daily.
       XXX Eventually make this configurable.
    '''
    outstr = ''
    showkeys = [ 'temperature', 'humidity', 'rain_daily' ]

    for stname in stations:
        st = stations[stname]

        outstr += '''
<fieldset class="stationbox">

<legend>%s</legend>

<table class="datatable">
<tr>
''' % (stname)

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
    '''Show details for just one station'''

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
        html_out += '<td>%s\n' % (field.replace('_', ' ').title())
        for stname in showstations:
            st = showstations[stname]

            # Not all stations have all fields, so be prepared
            # for a KeyError:
            try:
                # Time should normally be datetime.datetime.
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

def read_field_order_file():
    global field_order, field_order_fmt

    configfile = os.path.expanduser("~/.config/watchweather/fields")
    print("Trying to read fields from", configfile)

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

