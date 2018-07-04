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

export FLASK_APP=server/watchserver.py
flask run

For debug mode, first do:
export FLASK_DEBUG=1

You can view the station page in a browser:
http://127.0.0.1:5000/

Then add some stations:
client/stationreport.py Nearby
client/stationreport.py 'Far away'

You can modify client/stationreport to gather real temperature
data, or whatever other data you want.
