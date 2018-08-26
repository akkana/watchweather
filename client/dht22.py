#!/usr/bin/env python3

# Driver for a DHT11/DHT22 temperature/humidity sensor.

# The DHT22 is slightly more expensive but a little more accurate.

# Wiring:
#
# For a standalone DHT11/22 (4 pins), with the device's waffle section
# facing you, the pins from left are VDD, DATA, [UNUSED], GND.
# Use a 5-20k pullup resistor on DATA.
#
# For a DHT11 with a circuit board attached, there are only 3 pins,
# from left, DATA with a pullup already attached, VDD, GND.
# At least in theory; the only one I actually have seems to have
# a short and crashes my Pi as soon as it's plugged in.

# Usesse the Adafruit DHT library,
# https://github.com/adafruit/Adafruit_Python_DHT.git

import Adafruit_DHT

import time

MAXTRIES = 5

class DHTsensor:

    def __init__(self, sensortype=22, pin=4):
        '''Initialize with either a number (22, 11 or 2302)
           or a string like 'DHT
        '''
        if type(sensortype) is str:
            sensortype = sensortype.lower()
            if sensortype.endswith('11'):
                self.sensor = Adafruit_DHT.DHT11
            elif sensortype.endswith('2302'):
                self.sensor = Adafruit_DHT.AM2302
            else:
                self.sensor = Adafruit_DHT.DHT22
        elif sensortype == 11:
            self.sensor = Adafruit_DHT.DHT11
        elif sensortype == 2302:
            self.sensor = Adafruit_DHT.AM2302
        else:
            self.sensor = Adafruit_DHT.DHT22

        self.pin = pin

    def close(self):
        return

    def read_all(self):
        for i in range(MAXTRIES):
            humidity, temperature = Adafruit_DHT.read_retry(self.sensor,
                                                            self.pin)
            if humidity and temperature:
                break

            time.sleep(2.1)

        return { 'temperature' : temperature,
                 'humidity'    : humidity
        }

    def measurements_available(self):
        return None

if __name__ == '__main__':
    import sys
    print("len", len(sys.argv))
    if len(sys.argv) == 3:
        sensor = DHTsensor(sensortype=sys.argv[1], pin=int(sys.argv[2]))
    elif len(sys.argv) == 2:
        sensor = DHTsensor(sensortype=sys.argv[1])
    else:
        sensor = DHTsensor()

    print(sensor.read_all())
    sensor.close()


