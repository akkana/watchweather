# Server Notes

Instructions for testing this server are in the top-level README,
but eventually you'll probably want to set up a real server.
There are lots of
[http://flask.pocoo.org/docs/1.0/deploying/](Flask deployment options),
but most people are probably already running Apache. I found the mod-wsgi
instructions for Apache rather unclear, so here's what worked for me
on Debian Stretch.

## Testing the Server

To test the watchweather server, first create the needed configuration files:

```
mkdir ~/.config/watchweather/
cat >~/.config/watchweather/fields <<EOF
temperature
humidity
rain
EOF
```

If you want to test API calls, you may want to set
```
export WATCHWEATHER_KEY=[some long string]
```

If you've already been running watchweather on a server, you might
want to update your cache files:

```
rsync -av 'shallow:~watchweather/.cache/watchserver/' ~/.cache/watchserver/
```

or update them only with the latest from this year:

```
rsync -av 'shallow:~watchweather/.cache/watchserver/STATIONNAME-YYYY-*.csv' ~/.cache/watchserver/
```

Then run the server:

```
export FLASK_APP=server/watchserver.py
flask run
```

The key is optional for testing, but you should set it for production
so random people won't be able to trigger your API calls.

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


# Setting up Apache mod-wsgi on Debian:

To deploy watchweather in production, don't use the flask built-in
test server. Instead, set up WSGI with whatever web server you prefer.
Here are instructions for Apache2 on Debian:

First choose a user who will run watchweather, and make sure that user
has the required config file as specified in ../README.md.
You could, for example, create a user called "watchweather"
with a home directory of /var/www/watchweather (you might also
want to add your user to a group in /etc/group).
Or you can just use an existing user. Don't use root.

Create /etc/apache2/sites-available/watchweather-wsgi.conf with
(replace anything that includes YOUR):

```
<VirtualHost *:YOURPORT>
        ServerAdmin YOUR_ADDRSES
        DocumentRoot /var/www/YOURDIR

        ErrorLog ${APACHE_LOG_DIR}/YOURAPP-error.log
        CustomLog ${APACHE_LOG_DIR}/YOURAPP-access.log combined

        # wsgi-specific configuration
        # http://flask.pocoo.org/docs/1.0/deploying/mod_wsgi/
        WSGIDaemonProcess YOURAPP user=YOURUSER group=YOURGROUP threads=5
        WSGIScriptAlias / /var/www/YOURDIR/YOURAPP.wsgi

        <Directory /var/www/YOURAPP>
            WSGIProcessGroup YOURAPP
             WSGIApplicationGroup %{GLOBAL}
            Require all granted
        </Directory>

</VirtualHost>
```

There doesn't seem to be any convention on what port to use.

Symlink it into /etc/apache2/sites-enabled:
```
ln -s ../sites-available/YOURAPP-wsgi.conf /etc/apache2/sites-enabled/
```

Enable that port in *ports.conf*:
```
```
Listen YOURPORT

Create /var/www/YOURAPP containing something like this:

```
#!/usr/bin/env python3

import sys
sys.path.insert(0, '/YOURPATHTO/watchweather/server')

from watchserver import app as application
```

Now apt install libapache2-mod-wsgi-py3 (or libapache2-mod-wsgi
if you prefer to use python2, though watchserver isn't tested with
python2 and may need some tweaks).

Installing those packages should restart apache, but if not:

apache2ctl restart



