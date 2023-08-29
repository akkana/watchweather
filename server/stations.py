#!/usr/bin/env python3

# Manage a list of stations which are periodically reporting
# measured quantities such as temperature and humidity.

import os, sys
import json
import csv
from datetime import datetime, date, timedelta
import re


# The order in which to show fields.
# Read from ~/.config/watchweather/fields.
# There's one version with blanks in it, for pretty formatting,
# and another that's just the fields in order.
field_order = None
field_order_fmt = None


# A dictionary of dictionaries with various quantities we can report.
# The key in stations is station name.
# Dicts should include 'time' (datetime of last update).
# For example, station['office'] -> { 'temperature': 73, 'time': <datetime> }
# Values may be numbers or strings, but will normally be strings
# because that's what's sent in web requests.
stations = {}

# A dictionary of { "station_name": last_date }
last_station_update = {}

# How long to remember stations if they stop reporting.
expire_after = None

# Log files are named {savedir}/clientname-YYYY-MM-DD
# and contain CSV lines, with only the fields specified in field_order.
# If logging isn't wanted, set this to None in initialize().
# savedir will be ~/.cache/watchserver unless otherwise specified.
savedir = None

initialized = False


def initialize(expiration=None, savedir_path=None):
    """Initialize the station list.
       The optional expiration argument is a datetime.timedelta
       specifying how long to keep stations that stop reporting.
    """
    global savedir, expire_after, initialized
    if initialized:
        return

    if savedir_path:
        savedir = savedir_path
    else:
        savedir = os.path.expanduser("~/.cache/watchserver")

    if not os.path.exists(savedir):
        try:
            os.makedirs(savedir)
        except:
            print("LOGGING DISABLED: can't open %s" % savedir, file=sys.stderr)
            savedir = None

    if expiration:
        expire_after = expiration
    else:
        expire_after = timedelta(days=30)

    # Populate last_station_update with a list of anything that
    # has an entry in the savedir.
    # Also populate stations if the update hasn't expired.
    now = datetime.now()
    for csvfilename in sorted(os.listdir(savedir), reverse=True):
        # Valid filenames are like "Stationname-2021-08-27.csv"
        try:
            m = re.match(r'(.*)-(\d\d\d\d-\d\d-\d\d)\.csv', csvfilename)
            if not m:
                print("Illegal historic file", csvfilename, file=sys.stderr)
                continue
            stationname = m.group(1)

            # Seen this station already? Because of the reverse sort,
            # the first file seen is the most recent date, so
            # ignore any subsequent ones.
            if stationname in last_station_update:
                continue
            # there's no date.strptime, alas
            filedate = datetime.strptime(m.group(2), '%Y-%m-%d')
            last_station_update[stationname] = filedate

            if stationname not in stations:
                # date recent enough not to have expired?
                if now - filedate < expire_after:
                    # set values from the last line of the file,
                    # which is the most recent update
                    with open(os.path.join(savedir, csvfilename)) as csvfp:
                        reader = csv.DictReader(csvfp)
                        for row in reader:
                            pass    # ignore everything but the last row
                                    # XXX this should be done more efficiently

                    # Populate with the values from the last row
                    stations[stationname] = {}
                    for field in row:
                        if field == 'time':
                            stations[stationname][field] = \
                                datetime.strptime(row[field],
                                                  '%Y-%m-%d %H:%M:%S')
                            last_station_update[stationname] = \
                                stations[stationname][field]
                        else:
                            try:
                                stations[stationname][field] = \
                                    float(row[field])
                            except ValueError:
                                stations[stationname][field] = row[field]
                # else:
                #     print(stationname, ": last update was too old",
                #           filedate, "older than", expire_after)


        except Exception as e:
            print("Exception parsing filename %s: %s" % (csvfilename, e),
                  file=sys.stderr)
            continue


    # To get a list of bogus stations for testing, uncomment the next line:
    # populate_bogostations(5)

    initialized = True


def populate_bogostations(nstations):
    """Create a specified number of  bogus stations to test the web server.
       If you want to test layout, you probably want to create at least 5.
    """
    import random

    stationnames = [ 'office', 'patio', 'garden', 'garage', 'kitchen',
                     'bedroom', 'roof', 'living room', 'Death Valley',
                     'Antarctica' ]
    nstations = min(nstations, len(stationnames))
    for st in stationnames[:nstations]:
        stations[st] = { 'temperature': "%.1f" % (random.randint(65, 102)),
                         'humidity':    "%.1f" % (random.randint(1, 100) / 100),
                         'time' :       datetime.now()
                       }


# The idiot python json module can't handle datetimes,
# so those have to be treated specially:
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))


def parse(val):
    """Take a value, which might be a str, float, datetime or int,
       and parse it if it's a float or datetime since those will
       need reformatting.
    """
    if type(val) is not str:
        return val
    try:
        return int(val)
    except:
        pass
    try:
        return float(val)
    except:
        pass
    try:
        return datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
    except:
        pass
    try:
        return datetime.strptime(val, '%Y-%m-%d %H:%M:%S.%f')
    except:
        pass
    try:
        return datetime.strptime(val, '%Y-%m-%d %H:%M')
    except:
        pass
    return val


def update_station(station_name, station_data):
    """Update a station, adding it if it's new.
       station_data is a dictionary.
       Also prune the list of stations.
    """
    # station_data is all strings since it came in through JSON.
    # Parse it to something more useful.
    for key in station_data:
        if type(station_data[key]) is str:
            station_data[key] = parse(station_data[key])

    stations[station_name] = station_data

    # Make sure it's also in last_station_update
    last_station_update[station_name] = to_day(stations[station_name]['time'])

    if savedir:
        # files are named clientname-YYYY-MM-DD
        datafilename = os.path.join(savedir,
                                    "%s-%s.csv" % (station_name,
                           station_data['time'].strftime("%Y-%m-%d")))
        there_already =  os.path.exists(datafilename)

        with open(datafilename, "a") as datafp:
            # Write a header if the file was just created:
            if not there_already:
                print(','.join(get_field_order()), file=datafp)

            csvfields = []
            for field in field_order:
                if field not in station_data:
                    continue
                if field == 'time':
                    csvfields.append(station_data[field].strftime("%Y-%m-%d %H:%M:%S"))
                elif field in station_data:
                    csvfields.append(str(station_data[field]))
                else:
                    csvfields.append('')
            print(','.join(csvfields), file=datafp)

        # To write in JSONL instead:
        # with open(datafilename, "a") as datafp:
        #     datafp.write(json.dumps(station_data, default=json_serial))
        #     datafp.write('\n')

    prune_stations()


def prune_stations():
    """Remove any station that hasn't reported in a while.
    """
    now = datetime.now()
    deleted_stations = []
    for stname in stations:
        try:
            if now - stations[stname]['time'] > expire_after:
                deleted_stations.append(stname)
        except KeyError:
            print("No 'time' in station", stname, sys.stderr)
            pass

    for d in deleted_stations:
        del stations[d]


class StatField:
    """A field for accumulating numbers storing average, max, min.
    """

    def __init__(self):
        self.reset()

    def __repr__(self):
        if not self:
            return "<Empty StatField>"
        return """StatField:
total:   %.2f
number:  %d
average: %.2f
low:     %.2f
high:    %.2f""" % (self.total, self.n, self.average(), self.low, self.high)

    def __bool__(self):
        return (self.n > 0)

    def reset(self):
        self.total = 0
        self.n = 0
        self.low = sys.maxsize
        self.high = -sys.maxsize

    def set(self, val):
        self.total = val
        self.n = 1
        self.low = val
        self.high = val

    def accumulate(self, val):
        try:
            val = float(val)
            self.total += val
            self.n += 1
            self.low = min(self.low, val)
            self.high = max(self.high, val)
        except ValueError:
            pass

    def average(self):
        if not self.n:
            return None
        return self.total / self.n


def station_historic(stationname, days, chunkdays=1):
    """Build a historic summary for one station.
       days may be an integer number of days, or string "week", "month", "year"
       chunkdays controls how many lines to print, e.g.
       days="year" with chunksize=7 will print accumulated values for each week.
       chunkdays can also be "month" to show monthly totals.
       Return a list of dictionaries, keys "date", "Temperature Low", etc.
    """
    if not savedir:
        raise RuntimeError("No data dir, can't show historic summaries")

    lastdate = to_day(last_station_update[stationname])

    # Find the starting day based on days value
    if days == "week":
        days = 7
        day = (lastdate - timedelta(days=days))
    elif days == "month":
        # alas, there's no timedelta(months=1)
        if lastdate.month == 1:
            day = date(lastdate.year - 1, 12, lastdate.day)
        else:
            day = lastdate.replace(month=lastdate.month - 1)
    elif days == "year":
        day = lastdate.replace(year=lastdate.year - 1)
    else:
        days = int(days)
        day = (lastdate - timedelta(days=days))

    if chunkdays == 'month':
        # Beginning of the month following day
        month = day.month + 1
        year = day.year
        if month > 12:
            month = 1
            year += 1
        day = date(year, month, 1)
    else:
        try:
            chunkdays = int(chunkdays)
        except:
            print("Illegal value for chunkdays:", chunkdays, file=sys.stderr)
            chunkdays = 1

    # Fields that don't need any statistics: just take the last number.
    # Or, in case of chunking, sum the days-end "rain_daily" to "rain"
    # and skip the other rain fields.
    if chunkdays == 1:
        fields = [ "rain_daily", "rain_event", "rain_monthly", "rain_yearly" ]
    else:
        fields = [ "rain" ]

    retdata = []

    # A rainfall "event" means rain that has occurred without a break
    # of 24 hours or more. But that's tricky to calculate since the
    # most granular field is rain_hourly. So just use the last rain_daily
    # value for each day.
    rainfall_event = 0.
    last_rain_day = date(1970, 1, 1)

    # Show highs and lows for these fields
    highlowfields = { "temperature": None,
                      "average_wind": None,
                      "gust_speed": None
                    }
    # For some fields, lows are meaningless, it's always zero
    highs_only = ("average_wind", "gust_speed")

    curdic = {}

    def reset_fields(endday):
        """Save data accumulated over days, and reset
           to start new accumulations
        """
        nonlocal curdic

        # curdic always starts with at least one field, date
        # (necessary for date to be listed first in the HTML)
        # so just checking if curdic doesn't work.
        if curdic and len(curdic.keys()) > 1:
            # Date determination and formatting.
            # Associate the data in curdic with the last date in the window,
            # not the first. If this is averaged over more than one day,
            # show the range in a hopefully easily readable format.
            if chunkdays == 'month':
                curdic["date"] = "%s %s %02d-%02d" % (
                    curdic["date"].year, curdic["date"].strftime("%b"),
                    curdic["date"].day, endday.day)
            elif chunkdays > 1:
                curdic["date"] = "%s - %s" % (curdic["date"], str(endday))
            elif endday.day == 1:
                curdic["date"] = endday.strftime("%Y %b %-d")
            else:
                curdic["date"] = endday.strftime("%a %b %-d")

            retdata.append(curdic)

        for key in highlowfields:
            highlowfields[key] = StatField()
        # date field will be replaced by the last day, but the field
        # needs to be set first so it will show up first in the data
        # passed from cumulative() to timereport.html.
        # Save the actual date object, not the str of it,
        # so it can be formatted appropriately later.
        curdic = { "date": day }

    reset_fields(day)
    daychunk = 0

    while day <= lastdate:
        if chunkdays == 'month':
            if day.day == 1:
                yesterday = day - timedelta(days=1)
                reset_fields(yesterday)
                daychunk = 0
        elif daychunk >= chunkdays:
            # day is the first day *after* the chunk ends.
            # So pass yesterday's date.
            yesterday = day - timedelta(days=1)
            reset_fields(yesterday)
            daychunk = 0

        # Data files are named clientname-YYYY-MM-DD
        daystr = day.strftime("%Y-%m-%d")
        datafilename = os.path.join(savedir,
                                    "%s-%s.csv" % (stationname, daystr))
        try:
            with open(datafilename, "r") as datafp:
                reader = csv.DictReader(datafp)
                for row in reader:
                    for f in row:
                        try:
                            row[f] = float(row[f])
                            if f in highlowfields:
                                highlowfields[f].accumulate(row[f])
                        except:
                            continue
        except FileNotFoundError:
            # print("No file on", datafilename, file=sys.stderr)
            day += timedelta(days=1)
            continue

        # The last row contains the rainfall for the day
        if 'rain_daily' in row and row['rain_daily']:
            row['rain_daily'] = float(row['rain_daily'])
            rainfall_event += row['rain_daily']
            last_rain_day = day
            row["rain_event"] = rainfall_event
        else:
            rainfall_event = 0.

        # take "fields" from only the day's last row
        for f in fields:
            if f == "rain":
                if 'rain_daily' in row and row['rain_daily']:
                    if f not in curdic or not curdic[f]:
                        curdic[f] = 0.
                    curdic[f] += row['rain_daily']
                elif f not in curdic:
                    curdic[f] = 0.
            elif f in row and row[f]:
                curdic[f] = row[f]
            else:
                curdic[f] = None

        for f in highlowfields:
            if f not in highs_only:
                if highlowfields[f].low < sys.maxsize:
                    curdic[f + " low"] = highlowfields[f].low
                else:
                    curdic[f + " low"] = None
            if highlowfields[f].high > 0:
                curdic[f + " high"] = highlowfields[f].high
            else:
                curdic[f + " high"] = None

        day += timedelta(days=1)
        daychunk += 1

    reset_fields(lastdate)

    # Now get summaries: highest high, lowest low, total rain
    # print("historic data:")
    # from pprint import pprint
    # pprint(retdata)
    summaries = { "date": "Total\nLowest low\nHighest high" }
    for chunk in retdata:
        for key in chunk:
            if key == "date":
                continue
            if key not in summaries:
                summaries[key] = chunk[key]
                continue
            if key.endswith("low"):
                if chunk[key] < summaries[key]:
                    summaries[key] = chunk[key]
                continue
            if key.endswith("high"):
                if chunk[key] > summaries[key]:
                    summaries[key] = chunk[key]
                continue
            # If it doesn't have "low" or "high" in it, take a total sum
            summaries[key] += chunk[key]

    retdata.append(summaries)

    return retdata


def station_weekly(stationname):
    """Build a weekly summary for one station.
       Return a list of dictionaries, keys "date", "Temperature Low", etc.
    """
    return station_historic(stationname, days=7)


#
# Annoyingly, datetime doesn't offer a straightforward method
# for ensuring something is either a date or a datetime.
#
def to_day(dt):
    """Given datetime or date, return date"""
    if type(dt) is date:
        return dt
    return dt.date()


def to_datetime(d):
    """Given datetime or date, return datetime"""
    if type(d) is datetime:
        return d
    if type(d) is date:
        return datetime.combine(d, datetime.min.time())
    raise RuntimeError("Can't convert %s to datetime" % type(d))


def read_daily_data(stationname, valtypes, start_date, end_date):
    """Read the values from csv files that are already accumulated
       and so should not be summed,
       notably rain_daily and rain_event.
       No need to specify a time increment: it's always days.
       Return: {
           't':        [list of datetimes],
           'valtype1': [list of floats], ...
       }
    """
    retdata = { 't': [] }
    for vt in valtypes:
        retdata[vt] = []

    day = to_day(start_date)
    end_date = to_day(end_date)
    csvreader = None
    oneday = timedelta(days=1)

    while day <= end_date:
        daystr = day.strftime("%Y-%m-%d")
        datafilename = os.path.join(savedir,
                                    "%s-%s.csv" % (stationname, daystr))

        try:
            datafp = open(datafilename)
            csvreader = csv.DictReader(datafp)
            for row in csvreader:
                continue
            datafp.close()

            # Now row is the last row.
            retdata['t'].append(day)
            for vt in valtypes:
                try:
                    retdata[vt].append(float(row[vt]))
                except KeyError:
                    pass

        except FileNotFoundError:
            print("Skipping", day, ": no data file", sys.stderr)
            csvreader = None

        day += oneday

    # Were there any keys not found?
    for vt in valtypes:
        if vt not in retdata:
            print(f"Warning: no '{vt}' in the data", sys.stderr)

    return retdata


def read_csv_data_resample(stationname, valtypes,
                           start_time, end_time, time_incr):
    """Read the values from valtypes in from csv files,
       resampling to have values every time_incr (a datetime.timedelta)
       Return: {
           't':        [list of datetimes],
           'valtype1': [list of floats], ...
       }
    """
    retdata = { 't': [] }
    statdata = {}
    for vt in valtypes:
        retdata[vt] = []
        statdata[vt] = StatField()   # has n, total, low, high

    def average_this_interval():
        retdata["t"].append(t0)
        for vt in valtypes:
            if statdata[vt]:
                retdata[vt].append(statdata[vt].average())
            else:
                retdata[vt].append(None)

            statdata[vt].reset()

    start_time = to_datetime(start_time)
    end_time = to_datetime(end_time)
    t0 = to_datetime(start_time)
    t = t0
    t1 = t0 + time_incr
    end_day = to_day(end_time)

    csvreader = None
    day = None
    datafp = None

    while t <= end_time:
        if not csvreader:
            if datafp:
                datafp.close()

            # Prepare to read the next day's data
            if not day:
                day = to_day(start_time)
            # If day (from the previous iteration) >= end_day,
            # then the last file has already been read.
            elif day >= end_day:
                break
            else:
                day += timedelta(days=1)

            # Otherwise, try to open the next day's file.
            daystr = day.strftime("%Y-%m-%d")
            datafilename = os.path.join(savedir,
                                        "%s-%s.csv" % (stationname, daystr))
            try:
                datafp = open(datafilename)
                csvreader = csv.DictReader(datafp)
                t0 = to_datetime(max(to_datetime(day), start_time))
            except FileNotFoundError:
                # That means there's no data for this day,
                # so skip to the next day
                print("Skipping", day, ": no data file", sys.stderr)
                csvreader = None
                continue

        # Now there's definitely a csvreader object
        try:
            row = next(csvreader)
        except StopIteration:
            csvreader = None
            t0 += time_incr
            # Loop around and try again
            continue

        t = datetime.strptime(row['time'], "%Y-%m-%d %H:%M:%S")
        if t < t0:
            continue

        if t >= t1:
            # end of interval:
            # compute averages and save the new data items
            average_this_interval()

            t0 += time_incr
            t1 = t0 + time_incr
            if not t1 or t1 > end_time:
                t1 = end_time

        # Whether a new interval or old, accumulate this row.
        for vt in valtypes:
            statdata[vt].accumulate(row[vt])

    # Save the final averages
    if statdata[valtypes[0]]:
        average_this_interval()

    if datafp:
        datafp.close()

    return retdata


def compact_stations(stationname):
    """Rewrite historic data from past years into a more compact format.
       Write two sets of summary files:
       hourly, covering a month by hours, and daily, covering a year by days.
       Keep everything from the current year.
       Move summarized files to savedir/archived.

       Input datafiles are named servername-yyyy-mm-dd.csv
       Output datafiles are servername-yyyy-mm-hourly.csv
       and servername-yyyy-daily.csv
    """
    if not savedir:
        initialize()

    today = date.today()

    # Headers in the original 30-second data:
    orig_hdrs = [ "time", "temperature", "humidity",
                  "average_wind", "gust_speed", "max_gust", "wind_direction",
                  "rain",
                  # "rain_hourly", "rain_daily",
                  # "rain_weekly", "rain_monthly", "rain_yearly",
                  "absolute_pressure", # "relative_pressure",
                  "uv", "solar_radiation" ]
    # Headers for the summary files:
    stat_hdrs = [ "time", "min_temperature", "max_temperature",
                  "min_humidity", "max_humidity", "max_wind", "max_gust",
                  # "av_wind_direction", "stdev_wind_direction",
                  "rain",
                  "min_pressure", "max_pressure",
                  "max_uv", "max_solar_radiation" ]

    # Save the summary files in savedir, and
    # move the summarized files to this directory:
    archivedir = os.path.join(savedir, "archived")
    if not os.path.exists(archivedir):
        os.mkdir(archivedir)

    # Keep a list of files to move, but don't move them til the end
    files_summarized = []

    thisyear = date.today().year

    datafiles = os.listdir(savedir)
    datafiles.sort()

    # Accumulate hourly stats over the course of a month
    hourlystats = { "time": None }
    monthfp = None
    # and daily stats over the course of a year
    dailystats = { "time": None }
    yearfp = None

    # The date of the last file processed
    last_file_date = date(1970, 1, 1)

    def zero_stats(whichstats):
        # Starting a new chunk; initialize stat fields for every column
        # except time.
        for colname in orig_hdrs:
            if colname == 'time':
                whichstats[colname] = None
            else:
                whichstats[colname] = StatField()

    def write_stats(stats, fp):
        """Writes a dictionary of StatFields to the given file."""
        outdata = []
        # time
        outdata.append(stats["time"])

        # min_temperature
        outdata.append(f'{stats["temperature"].low}')
        # max_temperature
        outdata.append(f'{stats["temperature"].high}')
        # min_humidity
        outdata.append(f'{stats["humidity"].low}')
        # max_humidity
        outdata.append(f'{stats["humidity"].high}')

        # max_wind
        outdata.append(f'{stats["gust_speed"].high}')
        # max_gust
        outdata.append(f'{stats["max_gust"].high}')
        # av_wind_direction
        # outdata.append(f'{stats["wind_direction"].average(}'))
        # stdev_wind_direction
        # outdata.append(f'{stats["wind_direction"].std_dev(}'))

        # rain: daily vs. hourly has already been accounted for
        # outdata.append(f'{stats["rain_hourly"].total}')
        # outdata.append(f'{stats["rain_daily"].total}')
        outdata.append(f'{stats["rain"].total}')

        # min_pressure
        outdata.append(f'{stats["absolute_pressure"].low}')
        # max_pressure
        outdata.append(f'{stats["absolute_pressure"].high}')
        # max_uv
        outdata.append(f'{stats["uv"].high}')
        # max_solar_radiation
        outdata.append(f'{stats["solar_radiation"].high}')

        print(','.join(outdata), file=fp)


    stationstart = stationname + '-'
    stationstartlen = len(stationstart)
    yearfp = None
    monthfp = None
    for f in datafiles:
        if not f.startswith(stationstart):
            continue
        if not f.endswith(".csv"):
            continue
        filenameparts = f.split('.')[0].split('-')
            # [ stationname, year, month, day ] as strings
        file_date = date(*map(int, filenameparts[1:]))

        # New year? Close the current year output file and open a new one.
        if file_date.year != last_file_date.year:
            if yearfp:
                if dailystats["time"]:
                    write_stats(dailystats, yearfp)
                    write_stats(hourlystats, yearfp)
                yearfp.close()
                yearfp = None
                zero_stats(dailystats)
        if not yearfp:
            yearfile = "%s-%04d-daily.csv" % (stationname, file_date.year)
            yearfp = open(os.path.join(savedir, yearfile), 'w')
            print(','.join(stat_hdrs), file=yearfp)

        # New month? Close the current month output file and open a new one.
        if file_date.month != last_file_date.month:
            if monthfp:
                monthfp.close()
                monthfp = None
        if not monthfp:
            monthfile = "%s-%04d-%02d-hourly.csv" % (stationname,
                                                     file_date.year,
                                                     file_date.month)
            zero_stats(hourlystats)
            monthfp = open(os.path.join(savedir, monthfile), 'w')
            print(','.join(stat_hdrs), file=monthfp)

        # Loop over the daily files that typically store data every 30 seconds.
        # (Tried to use numpy, but np.genfromtxt is just too braindead
        # about reading data from CSV files and including a date field.)
        last_hour = -1
        with open(os.path.join(savedir, f)) as infp:
            reader = csv.DictReader(infp)
            for row in reader:
                t = datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S")
                # New day? Write and reset daily stats
                if t.date() != last_file_date:
                    if dailystats["time"]:
                        write_stats(dailystats, yearfp)
                    zero_stats(dailystats)
                    dailystats["time"] = "%04d-%02d-%02d %02d" % (
                        t.year, t.month, t.day, t.hour)

                if t.hour != last_hour:
                    # Done with an hour, time to summarize the last hour
                    if hourlystats["time"]:
                        write_stats(hourlystats, monthfp)
                    zero_stats(hourlystats)
                    hourlystats["time"] = "%04d-%02d-%02d %02d" % (
                        t.year, t.month, t.day, t.hour)

                for colname in orig_hdrs:
                    if colname == "time":
                        continue
                    try:
                        # Rainfall comes as hourly or daily chunks;
                        # accumulating more often than that results in
                        # multiple adds, so it's treated specially.
                        # Don't actually accumulate it, just replace it
                        # each time so at the end of the time period
                        # (day or hour) it will be the correct value.
                        if colname == "rain":
                            val = float(row["rain_hourly"])
                            hourlystats["rain"].set(val)
                            val = float(row["rain_daily"])
                            dailystats["rain"].set(val)
                        else:
                            val = float(row[colname])
                            hourlystats[colname].accumulate(val)
                            dailystats[colname].accumulate(val)
                    except:
                        # print("No value for", colname, "on", row["time"],
                        #       "in", f, ":", row[colname])
                        pass

                last_hour = t.hour
                last_file_date = file_date

            # Done with reading all the rows in day file f.
            if dailystats['time']:
                write_stats(dailystats, yearfp)
            if hourlystats['time']:
                write_stats(hourlystats, monthfp)

            infp.close()
            files_summarized.append(f)

    monthfp.close()
    yearfp.close()

    # Move files summarized to the archive
    for f in files_summarized:
        os.rename(os.path.join(savedir, f),
                  os.path.join(archivedir, f))


def get_field_order_fmt():
    if not field_order_fmt:
        read_field_order_file()

    return field_order_fmt


def get_field_order():
    global field_order

    if not field_order:
        field_order = [ f for f in get_field_order_fmt() if f ]

    return field_order


def read_field_order_file():
    global field_order_fmt

    configfile = os.path.expanduser("~/.config/watchweather/fields")

    try:
        with open(configfile) as fp:
            for line in fp:
                line = line.strip()
                if line.startswith('#'):
                    continue
                field_order_fmt.append(line)
        return field_order_fmt

    except:
        # Default field order
        field_order_fmt = [ "time",
                            "",
                            "temperature", "humidity",
                            "",
                            "average_wind", "gust_speed",
                            "max_gust", "wind_direction",
                            "",
                            "rain_hourly", "rain_daily", "rain_weekly",
                            "rain_monthly", "rain_yearly",
                            "",
                            "absolute_pressure", "relative_pressure",
                            "",
                            "uv", "solar_radiation"
                           ]

        # Add any extra fields that might be found in any stations
        for stname in stations:
            for f in stations[stname]:
                if f not in field_order_fmt:
                    field_order_fmt.append(f)


if __name__ == '__main__':
    initialize()
    print(stations_as_html())

