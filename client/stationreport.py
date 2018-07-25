#!/usr/bin/env python3

# Make reports from a distributed station with one or more sensors,
# such as temperature and humidity sensors.
# Requires the requests module.

import requests
import sys, os

def post_report(server, stationname, payload, port=None):
    if port:
        url = "http://%s:%d/report/%s" % (server, port, stationname)
    else:
        url = "http://%s/report/%s" % (server, stationname)

    return requests.post(url, data=payload)

def randomreport():
    import random

    temperature = random.randint(65, 102)
    humidity = random.randint(1, 100) / 100

    payload = {'temperature': str(temperature), 'humidity': str(humidity)}

    if len(sys.argv) > 1:
        r = post_report("127.0.0.1", sys.argv[1], payload, port=5000)
    else:
        r = post_report("127.0.0.1", "New Place", payload, port=5000)

def Usage():
    print('''Usage: %s stationname servername sensor

For debugging, use "test" for the sensorname''' % os.path.basename(sys.argv[0]))
    sys.exit(1)

if __name__ == '__main__':
    # Usage: stationport.py stationname servername sensor
    # If there are less than three arguments, make a random report instead
    # (for testing).

    if len(sys.argv) < 4:
        Usage()

    stationname = sys.argv[1]
    servername = sys.argv[2]
    sensorname = sys.argv[3]

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
        # measurements = sensor.measurements_available()
        # payload = {}
        # for m in measurements:
        #     val = measurements[m]()
        #     payload[m] = val
        sensor.close()

    try:
        r = post_report(servername, stationname, payload, port=5000)

        # If a station has sub-stations, post separate reports for them.
        # For instance, the observerscraper can collect data from
        # an outdoor2 and an indoor1 sensor.
        if hasattr(sensor, 'substations') and sensor.substations:
            for st in sensor.substations:
                payload = sensor.read_substation(st)
                post_report(servername, st, payload, port=5000)
    except requests.exceptions.ConnectionError:
        print("Couldn't post report. Is %s up?" % servername)
