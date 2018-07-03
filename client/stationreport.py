#!/usr/bin/env python3

import requests

def post_report(server, stationname, port=None):
    payload = {'temperature': '79', 'humidity': '7'}
    if port:
        url = "http://%s:%d/report/%s" % (server, port, stationname)
    else:
        url = "http://%s/report/%s" % (server, stationname)

    print("url:", url)
    return requests.post(url, data=payload)

if __name__ == '__main__':
    r = post_report("127.0.0.1", "office", port=5000)
    print(r)
    print(r.text)

