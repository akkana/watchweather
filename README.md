# watchweather

Display the output of multiple temperature stations on one page.

For instance, you can set up several Raspberry Pis around the house,
each with a temperature/humidity sensor, and display the output from
all of them on one page.

This is not limited to weather data: you could use the framework for
any quantities you want to report. It would be better to have a
more general name, and if I think of a good name I'll rename the
repository.

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

You can view the station page in a browser:
```
http://127.0.0.1:5000/
```

Then add some stations:
```
client/stationreport.py Nearby
client/stationreport.py 'Far away'
```

Or if you have stations with sensors, you can run them like this:
```
while true; do
  client/stationreport.py Bedroom hesiodus Si7021
  sleep 30
done
```

(Eventually the client will do its own looping.)

You can modify client/stationreport to gather real temperature
data, or whatever other data you want.

If you want to view the page in Firefox, you may have to go to
about:config, search for *refresh* and if *accessibility.blockautorefresh*
is true, double-click on that line to change it to false.
Supposedly the default is false but something is changing it to true
for a lot of people.
