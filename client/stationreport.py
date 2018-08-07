#!/usr/bin/env python3

# Make reports from a distributed station with one or more sensors,
# such as temperature and humidity sensors.
# Requires the requests module.

import requests
import argparse
import time
import sys, os

sensor = None
sensormodule = None

def initialize(sensorname):
    global sensormodule
    global sensor

    sensormodule = sensorname


    # Import the named module:
    sensormodule = __import__(sensorname)

    # call the initialization function of the same name as the module:
    sensor = getattr(sensormodule, sensorname)()

def stationreport(servername, stationname, port=5000, verbose=False,
                  test_client=None):
    '''Make a report to the server:port reflecting a particular station,
       based on what the sensor object is currently reporting.
       verbose will print debugging messages;
       test_client is used for automated testing since flask
       doesn't run a real server during unit tests.
    '''
    if verbose:
        if test_client:
            print("Trying a test report for '%s' with sensor '%s'"
                  % (stationname, sensormodule))
        else:
            print("Trying a report for '%s' with sensor '%s' to %s:%d"
                  % (stationname, sensormodule, servername, port))

    if not sensor:
        print("Sensor wasn't initialized")
        return

    try:
        payload = sensor.read_all()
    except Exception as e:
        print("Couldn't read sensor:", e)
        return

    if verbose:
        print("Payload to send to the server:", payload)

    # Ready to contact the server.
    try:
        # Was there a payload from the initial read_all()?
        if payload:
            r = post_report(servername, stationname, payload, port)

        # If a station has sub-stations, post separate reports for them.
        # For instance, the observerscraper can collect data from
        # an outdoor2 and an indoor1 sensor.
        if hasattr(sensor, 'substations') and sensor.substations:
            print("Substations:", sensor.substations)
            start = 1 if payload else 0
            for st in sensor.substations[start:]:
                payload = sensor.read_substation(st)
                post_report(servername, st, payload, port=port)
                if verbose:
                    print("Posted substation report for %s" % st)

        if verbose:
            print("Posted report")

    except requests.exceptions.ConnectionError:
        print("Couldn't post report. Is %s up?" % servername)

def post_report(server, stationname, payload, port):
    if port:
        url = "http://%s:%d/report/%s" % (server, port, stationname)
    else:
        url = "http://%s/report/%s" % (server, stationname)

    return requests.post(url, data=payload)

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

    if not args.port:
        args.port = 5000

    if args.verbose and args.loop:
        print("Looping with time %d" % args.loop)

    initialize(args.sensor)

    while True:
        stationreport(args.servername, args.stationname,
                      port=args.port, verbose=args.verbose)

        if not args.loop:
            sys.exit(0)

        time.sleep(args.loop)

