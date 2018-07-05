#!/usr/bin/env python3

import datetime

# A dictionary of dictionaries with various quantities we can report.
# The key in stations is station name.
# Dicts should include 'time' (datetime of last update).
# For example, station['office'] -> { 'temperature': 73, 'time': <datetime> }
# Values may be numbers or strings, but will normally be strings
# because that's what's sent in web requests.
stations = {}

def initialize():
    populate_bogostations(0)

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

def add_station(station_name, station_data):
    stations[station_name] = station_data
    # print("stations now:")
    # for st in stations:
    #     print(st)

def stations_as_html():
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
            outstr += '  <td>%s\n' % str(st[key])

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

