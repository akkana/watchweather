# Defining Sensors:

A sensor module named SensorName must provide the following:

```
sensor = SensorName.SensorName()      # Open and initialize the sensor

sensor.read_all()
   '''Read all values we know how to read, returning a dictionary, like
      { "temperature" : 78.2,
        "humidity"    : 22.4,
      }
      The values may be either strings or numbers.
   '''

sensor.measurements_available()
   # provides a dictionary of names and functions to be reported,
   # e.g.
   # { 'temperature', read_temperature_f() }

sensor.close()                        # This may be a no-op

```

