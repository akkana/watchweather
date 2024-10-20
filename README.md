# watchweather

Display the output of multiple temperature stations on one page.

For instance, you can set up several Raspberry Pis around the house,
each with a temperature/humidity sensor, and display the output from
all of them on one page, along with reports from your official weather
station or any other weather station that you can fetch via an API.
See the _client_ directory for types of weather reports supported
so far.

Reports are also logged, and there is a very limited facility for
reporting historic data. I hope to improve that eventually and add
graphs.

This is not limited to weather data: you could use the framework for
any quantities you want to check, report and log. It would be better to
have a more general name, and if I think of a good name I'll rename the
repository.

The server is based on flask. There are clients based on several
different sensors (suitable for running on Raspberry Pi) plus a scraper
for Ambient Weather stations (there's an attempt at reading data
directly from an ambient station in client/sdr_ambient.py, but I
never got the software defined radio to work reliably).

## Testing the Server

To test-run the server locally:

```
export FLASK_APP=server/watchserver.py
flask run
```

There's lots more detail on running the server, setting up bogus test data,
and various modes of running in server/README.md.

## Client Data Reporting

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

If your sensors are reporting correctly, you can make reports in a loop,
like this:

```
nohup client/stationreport.py -l Observer moon Si7021 &
```

or while debugging, you can do a simpler test, like:

```
while true; do
  client/stationreport.py Location servername Si7021
  sleep 30
done
```

You can also use -p port, if you need a port other than 5000,
and -v for verbose if you want to keep track of your reports.

For writing your own sensor, see the client/README.md.

## Viewing the Results

### Base page

The base page gives a simple list of options:

```
[http://localhost:5000/](http://localhost:5000/)
```


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

### /weekly/<stationname>

```
[http://localhost:5000/details/all](http://localhost:5000/details/all)
```

A table of selected data reported by the station in the last 7 days.
Useful for keeping track of quantities like daily rainfall that get
reset each day when you didn't stay glued to watchweather until midnight.

### /report/<stationname>

This is the page the clients use to make their reports.

### Auto-refresh in Firefox

Some pages, like /stations, auto-refresh.
Some versions of Firefox disable this by default.
To fix that, go to about:config, search for *refresh* and if
*accessibility.blockautorefresh* is true, double-click on that line to
change it to false. Supposedly the default is false but something is
changing it to true for me and a lot of people on the web.

## Testing

If you don't have any sensors yet and just want to test the server,
you can add some dummy station data using 'test' as the sensor name:
```
client/stationreport.py Nearby localhost testclient
client/stationreport.py 'Far away' localhost testclient
```

If you have a running instance on a server, with stored data, and you
want to test a local instance against that data, just copy the data over.
For instance, if you're running watchweather on a production server and
caching data in /var/www/watchweather/.cache, and locally you're using
the default of ~/.cache/watchweather, then:
```
rsync -av servername:/var/www/watchweather/.cache/watchserver/
```
