#!/usr/bin/env python3

# Get data using the Ambient Weather API.

import os
import requests
import json

fieldmap_main = {
    # 'dateutc':      '',
    'winddir':        'wind_direction',
    'windspeedmph':   'average_wind',
    'windgustmph':    'gust_speed',
    'maxdailygust':   'max_gust',
    'tempf':          'temperature',
    'humidity':       'humidity',
    'hourlyrainin':   'rain_hourly',
    'dailyrainin':    'rain_daily',
    'weeklyrainin':   'rain_weekly',
    'monthlyrainin':  'rain_monthly',
    'yearlyrainin':    'rain_yearly',
    'baromrelin':     'relative_pressure',
    'baromabsin':     'absolute_pressure',
    'uv': 'uv',
    'solarradiation': 'solar_radiation',
    # 'feelsLike':    '',
    # 'dewPoint':     '',
    # 'lastRain':     '',
    'date':           'time',
}

# The indoor sensor, in the console, only has temperature and humidity.
fieldmap_in = {
    'tempinf': 'temperature',
    'humidityin': 'humidity',
}

class ambient:

    def __init__(self):
        self.keys = {}
        self.outdata = {}
        self.indata = {}
        self.substations = []

        # Read the API keys
        keyfile = os.path.expanduser("~/.config/ambientweather/keys.conf")
        with open(keyfile) as fp:
            for line in fp:
                if '=' in line:
                    name, val = [ item.strip()
                                  for item in line.split('=', maxsplit=1) ]
                    self.keys[name] = val

    def close(self):
        return

    def read_all(self):
        # First tried this with string concatenation (remove the + signs)
        # and discovered a fun thing about the order of Python's
        # string concatenation.
        request_url = 'https://api.ambientweather.net/v1/devices?' \
                      + 'applicationKey=%s&' % self.keys['appkey'] \
                      + 'apiKey=%s' % self.keys['apikey']
        print("Request URL:", request_url)
        r = requests.get(request_url)
        self.data = json.loads(r.text)

        self.outdata = {}
        self.indata = {}

        print("data:")
        for d in self.data:
            print(d)
            print()

        # Report the first station:
        station = self.data[0]

        for field in station['lastData']:
            if field in fieldmap_main:
                    self.outdata[fieldmap_main[field]] \
                        = station['lastData'][field]
            if field in fieldmap_in:
                    self.indata[fieldmap_in[field]] \
                        = station['lastData'][field]

        self.substations = [ "Outdoor" ]
        if self.indata:
            self.substations.append("Indoor")

        # Do we have any other stations? Ambient is inconsistent
        # about whether it reports one or multiple stations for
        # a single weather station + console combination.
        if len(self.data) > 1:
            for station in self.data[1:]:
                print("Got an extra station", station['info']['name'])
                self.substations.append(station['info']['name'])

        # If there are multiple substations, don't return anything here,
        # we'll report as substations.
        return self.outdata

    def read_substation(self, subname):
        '''Assuming we've already read the main station and set self.outdata,
           return data just for the given substation.
        '''
        if subname not in self.substations:
            return None

        if subname == 'Indoor':
            return self.indata

        for station in self.data:
            if station['info']['name'] != subname:
                continue

            # We've found the right station. Remap the various fields.
            payload = {}
            for field in station['lastData']:
                if field in fieldmap:
                    payload[fieldmap[field]] = station['lastData'][field]

            return payload

        # We didn't find the right station.
        print("No such station '%s'" % subname)
        return None

    def measurements_available(self):
        return None

if __name__ == '__main__':
    sensor = ambient()
    print(sensor.read_all())
    sensor.close()

