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

# Running a client using systemd

Of course you can run a client by hand (recommended when testing),
or put it in /etc/rc.local. But you can use systemd to start it only
after the network is up, and to restart it automatically if it dies.

Create a file /lib/systemd/system/watchweather.service
containing something like this:

```
[Unit]
Description=Watchweather client
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Restart=always
ExecStart=/path/to/watchweather/client/stationreport.py -v -l 30 -p PORT NAME SERVERNAME SENSOR

[Install]
WantedBy=multi-user.target
```

SENSOR is the name of the sensor module in this directory, without
the .py extension: for instance, Si7021.

If you need the service to run as a specific user or group other than
root -- for example, if it needs to authenticate with a web API using
credentials stored in a file in ~/.config -- you can add them in the
[Service] section:

```
User=watchweather
Group=system
```

Then run:

```
sudo systemctl enable watchweather
sudo systemctl start watchweather
```

Output will show up in /var/log/daemon.log
