#!/usr/bin/env python3

# XXX youtube Fran's Dangerous Toys

# Test client for watchserver. Reports random temperature and humidity,
# and sometimes rainfall.

import random

class testclient:

    def __init__(self):
        self.temp = 85.
        self.humidity = 0.
        self.rain = 0

    def close(self):
        return

    def read_all(self):
        payload = { 'temperature' : self.temp,
                    'humidity'    : self.humidity,
                    'rain'        : self.rain
        }

        if random.randint(0, 4):
            self.temp += .2
            self.humidity -= .3
        else:
            self.rain += 0.1
            self.temp -= 1
            self.humidity += 1

        if self.temp > 104:
            self.temp = 95
        if self.humidity > 100:
            self.humidity = 100
        if self.humidity < 0:
            self.humidity = 0
        if self.rain < 0:
            self.rain = 0

        return payload

    def measurements_available(self):
        return None

if __name__ == '__main__':
    sensor = testclient()
    print(sensor.read_all())
    sensor.close()

