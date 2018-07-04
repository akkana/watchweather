#!/usr/bin/env python3

import datetime

# A list of dictionaries with various quantities we can report,
# which must include "name" and should include 'time' (datetime of last update).
# For example, station[0] might be { 'name': office, 'temperature': 73 }
# Values may be numbers or strings.
stations = []

def initialize():
    populate_bogostations()

def populate_bogostations():
    stations.append({ 'name': 'office',     'temperature': 73, 'humidity': 10 })
    stations.append({ 'name': 'patio',      'temperature': 73, 'humidity': 6 })
    stations.append({ 'name': 'bedroom',    'temperature': 73, 'humidity': 9 })
    stations.append({ 'name': 'guest room', 'temperature': 73, 'humidity': 12 })
    stations.append({ 'name': 'garden',     'temperature': 73, 'humidity': 4 })
    stations.append({ 'name': 'kitchen',    'temperature': 73, 'humidity': 7 })
    for st in stations:
        st['time'] = datetime.datetime.now()

def add_station(station_data):
    stations.append(station_data)
    print("stations now:")
    for st in stations:
        print(st)

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

