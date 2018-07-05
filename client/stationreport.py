#!/usr/bin/env python3

# Requires python3-requests

import requests
import sys

def post_report(server, stationname, payload, port=None):
    if port:
        url = "http://%s:%d/report/%s" % (server, port, stationname)
    else:
        url = "http://%s/report/%s" % (server, stationname)

    print("url:", url)
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

    print(r)
    print(r.text)

if __name__ == '__main__':
    # Usage: stationport.py stationname servername sensor
    # If there are less than three arguments, make a random report instead
    # (for testing).

    if len(sys.argv) < 4:
        randomreport()
        sys.exit(0)

    stationname = sys.argv[1]
    servername = sys.argv[2]
    sensorname = sys.argv[3]

    if sensorname == 'Si7021':
        import Si7021
        sensor = Si7021.Si7021(1)
        ctemp = sensor.read_temperature_c()
        ftemp = ctemp * 1.8 + 32
        humidity = sensor.read_humidity()
        payload = { 'temperature': "%.1f" % ftemp,
                    'humidity':    "%.1f" % humidity
                  }
        sensor.close()

        r = post_report(servername, stationname, payload, port=5000)

    elif sensorname == 'HTU21D':
        import HTU21D
        sensor = HTU21D.HTU21D()
        ctemp = sensor.read_tmperature()
        ftemp = ctemp * 1.8 + 32
        humidity = sensor.read_humidity()
        payload = { 'temperature': "%.1f" % ftemp,
                    'humidity':    "%.1f" % humidity
                  }

        r = post_report(servername, stationname, payload, port=5000)

    else:
        print("Unknown sensor", sensorname)
