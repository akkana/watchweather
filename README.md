# watchweather

Display the output of multiple temperature stations on one page.

For instance, you can set up several Raspberry Pis around the house,
each with a temperature/humidity sensor, and display the output from
all of them on one page.

This is not limited to weather data: you could use the framework for
any quantities you want to report. It would be better to have a
more general name, and if I think of a good name I'll rename the
repository.

## Running the Server

This is in an early stage of development. To test it, first run the server:

```
export FLASK_APP=server/watchserver.py
flask run
```

If you want to disable debug mode so you can access the server
from another machine:
```
flask run --host=0.0.0.0
```

For more debugging messages, try
```
export FLASK_DEBUG=1
```
though this is deceptive since debug *mode* is already on.

## Reporting some Data using Clients

The clients report data to the server using the program
client/stationreport.py.

There are several client modules in the client/ directory
that run on Raspberry Pi using sensors like Si7021 or HTU21D.

There's also a client module called observerscraper that scrapes the web page
from an Ambient Weather Observer. The Observer can have more than one
sensor (for instance, Outdoor and Indoor) so the observerscraper client
includes sub-stations which will make separate reports.

Run a single report by specifying which module you want to use, e.g.:
```
client/stationreport.py "Sensor Location" servername Si7021
```

If you don't have any sensors yet and just want to test the server,
you can add some stations using 'test' as the sensor name:
```
client/stationreport.py Nearby localhost test
client/stationreport.py 'Far away' localhost test
```

If your sensors are reporting correctly, you can make reports in a loop,
like this:

```
while true; do
  client/stationreport.py Location servername Si7021
  sleep 30
done
```

(Eventually the client will do its own looping.)

For writing your own sensor, see the client/README.md.

## Viewing the Results

### Base page

```
[http://localhost:5000/](http://localhost:5000/)
```

This gives a very minimalist menu of options.

### /stations

This is an overview that shows all stations in a pretty, large-text
format. It's good for keeping an eye on a few variables, like
temperature and pressure, for lots of stations. It's currently
not so good for stations that report a lot of variables.

```
[http://localhost:5000/stations](http://localhost:5000/stations)
```

### /details/<stationname>

```
[http://localhost:5000/details/all](http://localhost:5000/details/all)
```

This shows a table of all parameters known about a station.
It's better for stations like the observerscraper that report
a long list of values.

You can use "all" as the station name to see a table of all
stations that have reported.

### /report/<stationname>

This is the page the clients use to make their reports.

### Auto-refresh in Firefox

Some pages, like /stations, auto-refresh.
Some versions of Firefox disable this by default.
To fix that, go to about:config, search for *refresh* and if
*accessibility.blockautorefresh* is true, double-click on that line to
change it to false. Supposedly the default is false but something is
changing it to true for me and a lot of people on the web.


