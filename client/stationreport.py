#!/usr/bin/env python3

import requests
import sys

def post_report(server, stationname, payload, port=None):
    if port:
        url = "http://%s:%d/report/%s" % (server, port, stationname)
    else:
        url = "http://%s/report/%s" % (server, stationname)

    print("url:", url)
    return requests.post(url, data=payload)

if __name__ == '__main__':
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

