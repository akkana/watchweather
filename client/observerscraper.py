#!/usr/bin/env python3

# Scrape the web page from an Ambient Weather Observer.

import requests
from bs4 import BeautifulSoup
import sys, os
import re
import collections

def parse_value(s):
    '''Parse a string value, returning float, int or str as appropriate.
    '''
    # Figure out what type val is: float, int or string.
    try:
        val = int(s)
    except ValueError:
        try:
            val = float(s)
        except ValueError:
            val = s
    return val

def prettykey(key):
    if key in prettynames:
        return prettynames[key]
    print(key, "isn't in prettynames")
    return key

class observerscraper:
    def __init__(self):
        self.config = {
            'observerurl' : None,
            'wunderstation' : None,
        }
        self.fields = collections.OrderedDict()
        self.substations = {}
        self.outdata = None
        self.extradata = None

        dirs = [ os.path.expanduser("~/.config/watchweather"),
                 "/etc/watchweather" ]
        for d in dirs:
            self.read_config_file(os.path.join(d, 'observerscraper.config'))
            self.read_fields_file(os.path.join(d, 'observerscraper.fields'))

    def read_config_file(self, configfile):
        try:
            fp = open(configfile)
        except:
            return

        # print("Reading config from", configfile)
        for line in fp:
            line = line.strip()
            if line.startswith('#'):
                continue

            # Parse a substation line, if any. E.g.
            # substation My Indoor Sensor,inTemp,inHumi
            if line.startswith('substation'):
                parts = line[10:].strip().split(',')
                if len(parts) < 2:
                    print("Can't parse '%s'" % line)
                    continue

                self.substations[parts[0]] = parts[1:]
                continue

            parts = [ p.strip() for p in line.split('=') ]
            if not parts or len(parts) != 2:
                continue

            key = parts[0].lower()
            val = parts[1]

            self.config[key] = val

        fp.close()

    def read_fields_file(self, fieldsfile):
        '''Read the fields file, resulting in self.fields being an OrderedDict
           { 'CurrTime' : time, ..., 'ObserverKey' : 'watchweather-key' }
        '''
        try:
            fp = open(fieldsfile)
        except:
            return

        # print("Reading fields from", fieldsfile)
        for line in fp:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            pair = [ s.strip() for s in line.split(':') ]
            self.fields[pair[0]] = pair[1]

        fp.close()

    def close(self):
        return

    def read_all(self):
        print("Getting", self.config['observerurl'])
        r = requests.get(self.config['observerurl'])

        soup = BeautifulSoup(r.text, "lxml")

        self.outdata = {}
        self.extradata = {}

        for item in soup.find_all('input', type='text',
                                  class_=re.compile('item.*')):
            if 'name' not in item.attrs or 'value' not in item.attrs:
                print("\nThis item lacks name or value:", item)
                for key in item.attrs:
                    print("  %s: %s" % (key, item[key]))
                continue

            key = item['name']
            val = parse_value(item['value'])

            if key in self.fields:
                self.outdata[self.fields[key]] = val
            else:
                self.extradata[key] = val

        return self.outdata

    def read_substation(self, st):
        '''Assuming we've already read the main station and set self.outdata,
           return separate data for the given substation.
        '''
        sub_outdata = {}
        for field in self.substations[st]:
            if field.endswith('Temp'):
                sub_outdata['temperature'] = self.extradata[field]
            elif field.endswith('Humi'):
                sub_outdata['humidity'] = self.extradata[field]

        return sub_outdata

    def measurements_available(self):
        return None    # No individual measurement available

if __name__ == '__main__':
    vals = scrape_page(sys.argv[1])
    print("Got vals:", vals)
    for key in vals:
        print("%20s  %s" % (key, vals[key]))
