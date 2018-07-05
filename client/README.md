# Defining Sensors:

A sensor module named SensorName must provide the following:

```
sensor = SensorName.SensorName()      # Open and initialize the sensor

sensor.measurements_available(self)
   # provides a dictionary of names and functions to be reported,
   # e.g.
   # { 'temperature', read_temperature_f() }

sensor.close()                        # This may be a no-op

```

