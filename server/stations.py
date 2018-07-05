#!/usr/bin/env python3

# Manage a list of stations which are periodically reporting
# measured quantities such as temperature and humidity.

import datetime

# A dictionary of dictionaries with various quantities we can report.
# The key in stations is station name.
# Dicts should include 'time' (datetime of last update).
# For example, station['office'] -> { 'temperature': 73, 'time': <datetime> }
# Values may be numbers or strings, but will normally be strings
# because that's what's sent in web requests.
stations = {}

# How long to keep stations if they stop reporting:
expire_after = datetime.timedelta(minutes=15)

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

def update_station(station_name, station_data):
    '''Update a station, adding it if it's new.
       station_data is a dictionary.
       Also prune the list of stations.
    '''
    stations[station_name] = station_data
    # print("stations now:")
    # for st in stations:
    #     print(st)

    prune_stations()

def prune_stations():
    '''Remove any station that hasn't reported in a while.
    '''
    now = datetime.datetime.now()
    for stname in stations:
        try:
            if stations[stname]['time'] - now > expire_after:
                del stations[stname]
        except KeyError:
            print("No 'time' in station", stname)
            pass

def stations_as_html():
    '''Return an HTML string representing all the reporting stations.
    '''
    outstr = ''
    for stname in stations:
        st = stations[stname]

        outstr += '''
<fieldset class="stationbox">

<legend>%s</legend>

<table class="datatable">
<tr>
''' % (stname)

        keys = list(st.keys())

        # Keep the keys always in the same order.
        # Generally we want temperature first, so as a TEMPORARY measure,
        # use reverse sort. XXX Be smarter about order.
        keys.sort(reverse=True)

        for key in keys:
            if key == 'time':
                continue
            outstr += '  <td>%s\n' % key
        outstr += '<tr class="bigdata">'

        for key in keys:
            if key == 'time':
                continue

            # The value got here through http and is already a string.
            # However, if it's a floating point, chances are it has
            # way too many decimal places. To avoid depending on all
            # modules to do that properly, guard against it here.
            try:
                f = float(st[key])
                st[key] = '%.1f' % f
            except:
                pass

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

if __name__ == '__main__':
    initialize()
    print(stations_as_html())

