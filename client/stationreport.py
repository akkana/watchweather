#!/usr/bin/env python3

# Make reports from a distributed station with one or more sensors,
# such as temperature and humidity sensors.
# Requires the requests module.

import requests
import argparse
import time
import sys, os

def post_report(server, stationname, payload, port):
    if port:
        url = "http://%s:%d/report/%s" % (server, port, stationname)
    else:
        url = "http://%s/report/%s" % (server, stationname)

    return requests.post(url, data=payload)

def stationreport(servername, stationname, sensorname, port, verbose=False):
    if sensorname == 'test':
        import random
        payload = { 'temperature' : random.randint(65, 102),
                    'humidity'    : random.randint(1, 100) / 100
                  }

    else:
        # Import the named module:
        sensormodule = __import__(sensorname)
        # call the initialization function of the same name as the module:
        sensor = getattr(sensormodule, sensorname)()
        payload = sensor.read_all()
        sensor.close()

    if verbose:
        print("Trying a report for %s with sensor '%s' to %s:%d" % (stationname,
                                                                    sensorname,
                                                                    servername,
                                                                    port))

    try:
        r = post_report(servername, stationname, payload, port)
        if verbose:
            print("Posted report")

        # If a station has sub-stations, post separate reports for them.
        # For instance, the observerscraper can collect data from
        # an outdoor2 and an indoor1 sensor.
        if hasattr(sensor, 'substations') and sensor.substations:
            for st in sensor.substations:
                payload = sensor.read_substation(st)
                post_report(servername, st, payload, port=port)
                if verbose:
                    print("Posted substation report for %s" % st)

    except requests.exceptions.ConnectionError:
        print("Couldn't post report. Is %s up?" % servername)

if __name__ == '__main__':
    # Usage: stationport.py stationname servername sensor
    # If there are less than three arguments, make a random report instead
    # (for testing).

    parser = argparse.ArgumentParser()

    # Boolean flag
    # I'd like to allow -l without an argument, but then argparse
    # gets confused because the first positional argument, the stationname,
    # isn't an int and it's trying to use that for the loop value.
    # parser.add_argument('-l', '--loop', nargs='?', const=30, type=int,
    #                     help="Loop: repeat every l seconds (default 30)")
    # So instead, make it mandatory:
    parser.add_argument('-l', '--loop', type=int,
                        help="Loop: repeat every l seconds")
    parser.add_argument('-p', '--port', type=int,
                        help="Port (default: 5000)")
    parser.add_argument('-v', "--verbose", default=False,
                        action="store_true", help="Verbose")

    # Positional arguments:
    parser.add_argument("stationname",
                        help="The station name to use for reports")
    parser.add_argument("servername",
                        help="The name of the server (may be localhost)")
    parser.add_argument("sensor",
                        help="The sensor module to use, or 'test'")

    args = parser.parse_args(sys.argv[1:])

    print("args:", args)

    if not args.port:
        args.port = 5000

    if args.verbose and args.loop:
        print("Looping with time %d" % args.loop)

    while True:
        stationreport(args.servername, args.stationname, args.sensor,
                      port=args.port, verbose=args.verbose)

        if not args.loop:
            sys.exit(0)

        time.sleep(args.loop)

