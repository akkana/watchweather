#!/usr/bin/env python3

# Reads an Ambient Weather WS-2000 (or similar) station directly,
# using RTL-SDR, without needing to go through an observer or the API.

# A typical JSON reading:
# {"time" : "2019-01-11 11:50:12",
#  "model" : "Fine Offset WH65B",
#  "id" : 60,
#  "temperature_C" : 2.200,
#  "humidity" : 94,
#  "wind_dir_deg" : 316,
#  "wind_speed_ms" : 0.064,
#  "gust_speed_ms" : 0.510,
#  "rainfall_mm" : 90.678,    # Cumulative starting at some unknown time
#  "uv" : 324, "uvi" : 0,
#  "light_lux" : 19344.000,
#  "battery" : "OK",
#  "mic" : "CRC"}

import subprocess
import json


fieldmap = {
    # sensor_field    returned_field
    "temperature_C":  "temperature",
    "humidity" : 'humidity',
    "wind_dir_deg" : 'wind_direction',
    "wind_speed_ms" : 'average_wind',
    "gust_speed_ms" : 'gust_speed',
    # "rainfall_mm" :
    "uv" : 'uv',
    # "uvi" :
    "light_lux" : 'solar_radiation',
}


class sdr_ambient:
    def __init__(self):
        # universal_newlines=True is needed for readline() in realtime.
        # It also apparently converts the output from bytes into strings.
        self.proc = subprocess.Popen(['rtl_433', '-f', '915M',
                                      # '-s', '2400000',
                                      '-F', 'json'],
                                     universal_newlines=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
        # while True:
        #     line = self.proc.stdout.readline()
        #     line = line.strip()
        #     print("Initial line: '%s'" % line)
        #     if line.startswith('{') and line.endswith('}'):
        #         # we've gotten past the initial stuff
        #         # and are now emitting JSON
        #         print("braces, breaking")
        #         break
        # Commented out; just ignore the initial stuff in stderr

        # The WH65B reports rainfall as a long-running accumulation.
        # Starting from when? There's no telling. But the important
        # thing is keeping track of what it was at the start.
        # So null it here and set it after the first report.
        self.rainfall_start = None

    def close(self):
        self.proc.terminate()
        # print("Waiting for process to terminate ...")
        try:
            self.proc.wait(10)
        except subprocess.TimeoutExpired:
            print("Timeout expired, process %d isn't terminating"
                  % self.proc.pid)
        return

    def read_all(self):
        line = self.proc.stdout.readline().strip()
        print("Read a line:", line)
        vals = json.loads(line)
        print("vals:", vals)
        outvals = {}

        for field in vals:
            if field == 'rainfall_mm':
                rainfall = float(vals['rainfall_mm'])

                if self.rainfall_start:
                    outvals['rain_yearly'] = rainfall - self.rainfall_start
                self.rainfall_start = rainfall

            elif field in fieldmap:
                outvals[fieldmap[field]] = vals[field]

        print("Returning:", outvals)
        return outvals


if __name__ == '__main__':
    sensor = sdr_ambient()
    print(sensor.read_all())
    sensor.close()


