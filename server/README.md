# Server Notes

Instructions for testing this server are in the top-level README,
but eventually you'll probably want to set up a real server.
There are lots of
[http://flask.pocoo.org/docs/1.0/deploying/](Flask deployment options),
but most people are probably already running Apache. I found the mod-wsgi
instructions for Apache rather unclear, so here's what worked for me
on Debian Stretch.

# Setting up mod-wsgi on Debian:

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

On Debian, install libapache2-mod-wsgi-py3 (or libapache2-mod-wsgi
if you prefer to use python2, though watchserver isn't tested with
python2 and may need some tweaks).

Installing those packages should restart apache, but if not:

apache2ctl restart



